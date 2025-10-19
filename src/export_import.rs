use crate::models::Person;
use crate::file_manager::FileManager;
use anyhow::{Result, Context};
use std::path::Path;
use std::fs;
use zip::ZipWriter;
use zip::write::FileOptions;
use std::io::{Read, Write};

#[derive(Clone)]
pub struct ExportImportManager {
    file_manager: FileManager,
}

impl ExportImportManager {
    pub fn new(file_manager: FileManager) -> Self {
        Self { file_manager }
    }

    pub fn export_to_ema(&self, output_path: &Path, persons: &[Person], progress_callback: Option<Box<dyn Fn(String) + Send + Sync>>) -> Result<()> {
        // Create the zip file
        let file = fs::File::create(output_path)
            .context("Failed to create output file")?;
        let mut zip = ZipWriter::new(file);

        let evidence_dir = self.file_manager.get_evidence_dir();
        
        // Count total files for progress tracking
        let mut total_files = 0;
        let mut processed_files = 0;
        
        // First pass: count total files for selected persons only
        for person in persons {
            let person_dir = evidence_dir.join(person.folder_name());
            if person_dir.exists() {
                for entry in walkdir::WalkDir::new(&person_dir) {
                    let entry = entry.context("Failed to read directory entry")?;
                    if entry.file_type().is_file() {
                        total_files += 1;
                    }
                }
            }
        }
        
        // Second pass: add files for selected persons only
        for person in persons {
            let person_dir = evidence_dir.join(person.folder_name());
            if person_dir.exists() {
                for entry in walkdir::WalkDir::new(&person_dir) {
                    let entry = entry.context("Failed to read directory entry")?;
                    let path = entry.path();
                    
                    if entry.file_type().is_file() {
                        let relative_path = path.strip_prefix(evidence_dir)
                            .context("Failed to strip evidence directory prefix")?;
                        
                        let zip_path = relative_path.to_string_lossy().replace('\\', "/");
                        
                        zip.start_file(&zip_path, FileOptions::default())
                            .context("Failed to start file in zip")?;
                        
                        let file_content = fs::read(path)
                            .context("Failed to read file")?;
                        
                        zip.write_all(&file_content)
                            .context("Failed to write file to zip")?;
                        
                        processed_files += 1;
                        
                        if let Some(ref callback) = progress_callback {
                            let progress = (processed_files as f32 / total_files as f32 * 100.0) as u32;
                            callback(format!("Exporting... {}%", progress));
                        }
                    }
                }
            }
        }

        zip.finish()
            .context("Failed to finish zip file")?;

        Ok(())
    }

    pub fn import_from_ema(&self, input_path: &Path, progress_callback: Option<Box<dyn Fn(String) + Send + Sync>>) -> Result<Vec<Person>> {
        let file = fs::File::open(input_path)
            .context("Failed to open input file")?;
        let mut zip = zip::ZipArchive::new(file)
            .context("Failed to read zip file")?;

        let evidence_dir = self.file_manager.get_evidence_dir();
        let mut persons = Vec::new();
        
        let total_files = zip.len();
        
        // Extract all files directly to the Evidence directory
        for i in 0..total_files {
            let mut file = zip.by_index(i)
                .context("Failed to read file from zip")?;
            
            if let Some(ref callback) = progress_callback {
                let progress = ((i + 1) as f32 / total_files as f32 * 100.0) as u32;
                callback(format!("Importing... {}%", progress));
            }
            
            let outpath = match file.enclosed_name() {
                Some(path) => evidence_dir.join(path),
                None => continue,
            };
            
            // Ensure the target directory exists
            if let Some(parent) = outpath.parent() {
                fs::create_dir_all(parent)
                    .context("Failed to create target directory")?;
            }
            
            // Extract the file
            let mut file_content = Vec::new();
            file.read_to_end(&mut file_content)
                .context("Failed to read file from zip")?;
            
            fs::write(&outpath, file_content)
                .context("Failed to write extracted file")?;
        }
        
        // Now load all persons from the extracted data and ensure all subdirectories exist
        for entry in fs::read_dir(&evidence_dir)
            .context("Failed to read Evidence directory")?
        {
            let entry = entry.context("Failed to read directory entry")?;
            let path = entry.path();

            if path.is_dir() && path.file_name().and_then(|n| n.to_str()).map(|s| s != ".").unwrap_or(false) {
                if let Ok(person) = self.file_manager.load_person_data(&path) {
                    // Ensure all required subdirectories exist for this person
                    self.ensure_person_subdirectories(&person)?;
                    persons.push(person);
                }
            }
        }

        Ok(persons)
    }

    /// Ensures all required subdirectories exist for a person
    fn ensure_person_subdirectories(&self, person: &Person) -> Result<()> {
        use crate::models::EvidenceType;
        
        let person_folder = self.file_manager.get_evidence_dir().join(person.folder_name());
        
        // Create all required subdirectories
        for evidence_type in [EvidenceType::Image, EvidenceType::Audio, EvidenceType::Video, EvidenceType::Document, EvidenceType::Quote] {
            let subfolder = person_folder.join(evidence_type.folder_name());
            fs::create_dir_all(&subfolder)
                .context("Failed to create evidence subfolder")?;
        }
        
        Ok(())
    }

}
