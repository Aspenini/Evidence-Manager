use crate::models::{Person, EvidenceFile, EvidenceType};
use anyhow::{Result, Context};
use std::path::{Path, PathBuf};
use std::fs;
use walkdir::WalkDir;
use chrono::Utc;
use uuid::Uuid;

#[derive(Clone)]
pub struct FileManager {
    evidence_dir: PathBuf,
}

impl FileManager {
    pub fn new() -> Result<Self> {
        let exe_dir = std::env::current_exe()
            .context("Failed to get current executable path")?
            .parent()
            .context("Executable has no parent directory")?
            .to_path_buf();
        
        let evidence_dir = exe_dir.join("Evidence");
        fs::create_dir_all(&evidence_dir)
            .context("Failed to create Evidence directory")?;

        Ok(Self { evidence_dir })
    }

    pub fn get_evidence_dir(&self) -> &Path {
        &self.evidence_dir
    }

    pub fn create_person_folder(&self, person: &Person) -> Result<PathBuf> {
        let person_folder = self.evidence_dir.join(person.folder_name());
        
        if !person_folder.exists() {
            fs::create_dir_all(&person_folder)
                .context("Failed to create person folder")?;
            
            // Create subfolders for different media types
            for evidence_type in [EvidenceType::Image, EvidenceType::Audio, EvidenceType::Video, EvidenceType::Document, EvidenceType::Quote] {
                let subfolder = person_folder.join(evidence_type.folder_name());
                fs::create_dir_all(&subfolder)
                    .context("Failed to create evidence subfolder")?;
            }
        }

        Ok(person_folder)
    }

    pub fn save_person_data(&self, person: &Person) -> Result<()> {
        let person_folder = self.create_person_folder(person)?;
        let person_data_file = person_folder.join("person_data.json");
        
        let json = serde_json::to_string_pretty(person)
            .context("Failed to serialize person data")?;
        
        fs::write(&person_data_file, json)
            .context("Failed to write person data file")?;

        Ok(())
    }

    pub fn load_person_data(&self, person_folder: &Path) -> Result<Person> {
        let person_data_file = person_folder.join("person_data.json");
        
        if !person_data_file.exists() {
            return Err(anyhow::anyhow!("Person data file not found"));
        }

        let json = fs::read_to_string(&person_data_file)
            .context("Failed to read person data file")?;
        
        let person: Person = serde_json::from_str(&json)
            .context("Failed to parse person data")?;

        Ok(person)
    }

    pub fn load_all_persons(&self) -> Result<Vec<Person>> {
        let mut persons = Vec::new();

        for entry in fs::read_dir(&self.evidence_dir)
            .context("Failed to read Evidence directory")?
        {
            let entry = entry.context("Failed to read directory entry")?;
            let path = entry.path();

            if path.is_dir() && path.file_name().and_then(|n| n.to_str()).map(|s| s != ".").unwrap_or(false) {
                if let Ok(person) = self.load_person_data(&path) {
                    persons.push(person);
                }
            }
        }

        Ok(persons)
    }

    pub fn delete_person(&self, person: &Person) -> Result<()> {
        let person_folder = self.evidence_dir.join(person.folder_name());
        
        if person_folder.exists() {
            fs::remove_dir_all(&person_folder)
                .context("Failed to delete person folder")?;
        }

        Ok(())
    }

    pub fn copy_file_to_evidence(&self, person: &Person, source_path: &Path, evidence_type: EvidenceType) -> Result<EvidenceFile> {
        let person_folder = self.create_person_folder(person)?;
        let target_folder = person_folder.join(evidence_type.folder_name());
        
        let file_name = source_path.file_name()
            .context("Source file has no name")?
            .to_string_lossy();
        
        let target_path = target_folder.join(&*file_name);
        
        // Handle duplicate file names
        let mut final_path = target_path.clone();
        let mut counter = 1;
        while final_path.exists() {
            let stem = source_path.file_stem()
                .context("Source file has no stem")?
                .to_string_lossy();
            let extension = source_path.extension()
                .context("Source file has no extension")?
                .to_string_lossy();
            
            let new_name = format!("{}_{}.{}", stem, counter, extension);
            final_path = target_folder.join(new_name);
            counter += 1;
        }

        fs::copy(source_path, &final_path)
            .context("Failed to copy file to evidence folder")?;

        let metadata = fs::metadata(&final_path)
            .context("Failed to get file metadata")?;

        Ok(EvidenceFile {
            id: Uuid::new_v4(),
            person_id: person.id,
            file_path: final_path,
            file_type: evidence_type,
            original_name: file_name.to_string(),
            size: metadata.len(),
            created_at: Utc::now(),
            notes: String::new(),
        })
    }

    pub fn scan_person_evidence(&self, person: &Person) -> Result<Vec<EvidenceFile>> {
        let person_folder = self.evidence_dir.join(person.folder_name());
        let mut evidence_files = Vec::new();

        if !person_folder.exists() {
            return Ok(evidence_files);
        }

        for entry in WalkDir::new(&person_folder)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
        {
            let path = entry.path();
            let relative_path = path.strip_prefix(&person_folder)
                .context("Failed to strip prefix")?;

            // Skip person_data.json
            if relative_path.file_name().and_then(|n| n.to_str()) == Some("person_data.json") {
                continue;
            }

            if let Some(extension) = path.extension() {
                if let Some(evidence_type) = EvidenceType::from_extension(extension.to_string_lossy().as_ref()) {
                    let metadata = fs::metadata(path)
                        .context("Failed to get file metadata")?;

                    evidence_files.push(EvidenceFile {
                        id: Uuid::new_v4(),
                        person_id: person.id,
                        file_path: path.to_path_buf(),
                        file_type: evidence_type,
                        original_name: path.file_name()
                            .context("File has no name")?
                            .to_string_lossy()
                            .to_string(),
                        size: metadata.len(),
                        created_at: metadata.created()
                            .ok()
                            .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                            .map(|d| chrono::DateTime::from_timestamp(d.as_secs() as i64, 0).unwrap_or_else(Utc::now))
                            .unwrap_or_else(Utc::now),
                        notes: String::new(),
                    });
                }
            }
        }

        Ok(evidence_files)
    }
}
