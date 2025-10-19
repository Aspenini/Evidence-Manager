use crate::export_import::ExportImportManager;
use crate::file_manager::FileManager;
use crate::models::{EvidenceFile, EvidenceType, Person};
use anyhow::{anyhow, Context, Result};
use std::path::Path;
use std::sync::Mutex;
use uuid::Uuid;

pub struct AppState {
    inner: Mutex<BackendState>,
}

impl AppState {
    pub fn new() -> Result<Self> {
        let file_manager = FileManager::new()?;
        let export_import_manager = ExportImportManager::new(file_manager.clone());
        let persons = file_manager.load_all_persons().unwrap_or_default();

        Ok(Self {
            inner: Mutex::new(BackendState {
                file_manager,
                export_import_manager,
                persons,
            }),
        })
    }

    pub fn lock(&self) -> Result<std::sync::MutexGuard<'_, BackendState>> {
        self.inner.lock().map_err(|_| anyhow!("State poisoned"))
    }
}

pub struct BackendState {
    pub(crate) file_manager: FileManager,
    pub(crate) export_import_manager: ExportImportManager,
    pub(crate) persons: Vec<Person>,
}

impl BackendState {
    pub fn list_persons(&self) -> Vec<Person> {
        self.persons.clone()
    }

    pub fn get_person_mut(&mut self, id: Uuid) -> Result<&mut Person> {
        self.persons
            .iter_mut()
            .find(|person| person.id == id)
            .context("Person not found")
    }

    pub fn get_person(&self, id: Uuid) -> Result<&Person> {
        self.persons
            .iter()
            .find(|person| person.id == id)
            .context("Person not found")
    }

    pub fn save_person(&mut self, person: &Person) -> Result<()> {
        self.file_manager.save_person_data(person)
    }

    pub fn delete_person(&mut self, id: Uuid) -> Result<()> {
        let person = self.get_person(id)?.clone();
        self.file_manager.delete_person(&person)?;
        self.persons.retain(|p| p.id != id);
        Ok(())
    }

    pub fn add_person(&mut self, name: String) -> Result<Person> {
        let mut person = Person::new(name);
        self.file_manager.create_person_folder(&person)?;
        self.file_manager.save_person_data(&person)?;
        self.persons.push(person.clone());
        Ok(person)
    }

    pub fn scan_evidence(&self, person_id: Uuid) -> Result<Vec<EvidenceFile>> {
        let person = self.get_person(person_id)?;
        self.file_manager.scan_person_evidence(person)
    }

    pub fn copy_evidence(
        &mut self,
        person_id: Uuid,
        source_path: &Path,
        evidence_type: EvidenceType,
    ) -> Result<EvidenceFile> {
        let person = self.get_person(person_id)?.clone();
        let evidence =
            self.file_manager
                .copy_file_to_evidence(&person, source_path, evidence_type)?;
        // Rescan evidence to keep UI in sync
        Ok(evidence)
    }
}
