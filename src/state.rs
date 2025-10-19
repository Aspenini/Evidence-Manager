use crate::models::{Person, EvidenceFile, EvidenceType};
use crate::file_manager::FileManager;
use crate::export_import::ExportImportManager;
use crate::gui::EvidenceTab;
use iced::{
    Application, Command, Element, Theme, executor, Subscription,
};
use std::path::PathBuf;
use uuid::Uuid;
use anyhow::Result;

#[derive(Debug, Clone)]
pub enum Message {
    // Person management
    PersonSelected(Uuid),
    AddPersonClicked,
    AddPersonNameChanged(String),
    AddPersonSubmitted,
    DeletePerson(Uuid),
    
    // Information management
    AddInfoTypeChanged(String),
    AddInfoValueChanged(String),
    AddInfoSubmitted,
    RemoveInfo(Uuid),
    
    // Quote management
    AddQuoteTextChanged(String),
    AddQuoteDateChanged(String),
    AddQuoteTimeChanged(String),
    AddQuotePlaceChanged(String),
    AddQuoteSubmitted,
    RemoveQuote(Uuid),
    
    // Tab navigation
    TabChanged(EvidenceTab),
    
    // File operations
    SelectFileClicked,
    FileSelected(PathBuf),
    FileAddedSuccessfully,
    ImportClicked,
    ExportClicked,
    ImportFileSelected(PathBuf),
    ExportFileSelected(PathBuf),
    
    // Async operations
    ImportComplete(Result<Vec<Person>, String>),
    ExportComplete(Result<(), String>),
    PersonAdded(Result<Person, String>),
    PersonDeleted(Result<(), String>),
    InfoAdded(Result<(), String>),
    InfoRemoved(Result<(), String>),
    QuoteAdded(Result<(), String>),
    QuoteRemoved(Result<(), String>),
    
    // UI state
    SearchQueryChanged(String),
    ShowAddPersonDialog(bool),
    ShowImportDialog(bool),
    ShowExportDialog(bool),
    
    // Status
    StatusMessage(String),
}

pub struct AppState {
    // Backend
    file_manager: FileManager,
    export_import_manager: ExportImportManager,
    
    // Data
    pub persons: Vec<Person>,
    pub selected_person: Option<Uuid>,
    pub evidence_files: Vec<EvidenceFile>,
    
    // UI State
    pub current_tab: EvidenceTab,
    pub search_query: String,
    pub filtered_persons: Vec<Uuid>,
    
    // Dialog states
    pub show_add_person_dialog: bool,
    pub show_import_dialog: bool,
    pub show_export_dialog: bool,
    
    // Form fields
    pub new_person_name: String,
    pub new_info_type: String,
    pub new_info_value: String,
    pub new_quote_text: String,
    pub new_quote_date: String,
    pub new_quote_time: String,
    pub new_quote_place: String,
    
    // Status
    pub status_message: String,
    pub status_timeout: f32,
}

impl AppState {
    pub fn new() -> Result<Self> {
        let file_manager = FileManager::new()?;
        let export_import_manager = ExportImportManager::new(file_manager.clone());
        let persons = file_manager.load_all_persons().unwrap_or_default();
        
        Ok(Self {
            file_manager,
            export_import_manager,
            persons,
            selected_person: None,
            evidence_files: Vec::new(),
            current_tab: EvidenceTab::Information,
            search_query: String::new(),
            filtered_persons: Vec::new(),
            show_add_person_dialog: false,
            show_import_dialog: false,
            show_export_dialog: false,
            new_person_name: String::new(),
            new_info_type: String::new(),
            new_info_value: String::new(),
            new_quote_text: String::new(),
            new_quote_date: String::new(),
            new_quote_time: String::new(),
            new_quote_place: String::new(),
            status_message: String::new(),
            status_timeout: 0.0,
        })
    }
    
    fn update_filtered_persons(&mut self) {
        if self.search_query.is_empty() {
            self.filtered_persons = self.persons.iter().map(|p| p.id).collect();
        } else {
            self.filtered_persons = self.persons
                .iter()
                .filter(|p| p.name.to_lowercase().contains(&self.search_query.to_lowercase()))
                .map(|p| p.id)
                .collect();
        }
    }
    
    fn update_status(&mut self, message: String) {
        self.status_message = message;
        self.status_timeout = 5.0;
    }
    
    
    pub fn refresh_evidence_files(&mut self) {
        if let Some(person_id) = self.selected_person {
            if let Some(person) = self.persons.iter().find(|p| p.id == person_id) {
                match self.file_manager.scan_person_evidence(person) {
                    Ok(files) => self.evidence_files = files,
                    Err(_) => self.evidence_files.clear(),
                }
            }
        } else {
            self.evidence_files.clear();
        }
    }
}

impl Application for AppState {
    type Executor = executor::Default;
    type Message = Message;
    type Theme = Theme;
    type Flags = ();

    fn new(_flags: ()) -> (Self, Command<Message>) {
        match Self::new() {
            Ok(mut state) => {
                state.update_filtered_persons();
                (state, Command::none())
            }
            Err(e) => {
                eprintln!("Failed to initialize application: {}", e);
                std::process::exit(1);
            }
        }
    }

    fn title(&self) -> String {
        String::from("Evidence Manager")
    }

    fn update(&mut self, message: Message) -> Command<Message> {
        match message {
            Message::PersonSelected(id) => {
                self.selected_person = Some(id);
                self.refresh_evidence_files();
                Command::none()
            }
            
            Message::AddPersonClicked => {
                self.show_add_person_dialog = true;
                Command::none()
            }
            
            Message::AddPersonNameChanged(name) => {
                self.new_person_name = name;
                Command::none()
            }
            
            Message::AddPersonSubmitted => {
                if !self.new_person_name.trim().is_empty() {
                    let name = self.new_person_name.trim().to_string();
                    self.new_person_name.clear();
                    self.show_add_person_dialog = false;
                    
                    let file_manager = self.file_manager.clone();
                    Command::perform(
                        async move {
                            let person = Person::new(name);
                            file_manager.save_person_data(&person).map(|_| person).map_err(|e| e.to_string())
                        },
                        Message::PersonAdded
                    )
                } else {
                    Command::none()
                }
            }
            
            Message::PersonAdded(result) => {
                match result {
                    Ok(person) => {
                        self.persons.push(person);
                        self.persons.sort_by(|a, b| a.name.cmp(&b.name));
                        self.update_filtered_persons();
                        self.update_status("Person successfully added".to_string());
                    }
                    Err(e) => {
                        self.update_status(format!("Failed to add person: {}", e));
                    }
                }
                Command::none()
            }
            
            Message::DeletePerson(id) => {
                if let Some(person) = self.persons.iter().find(|p| p.id == id) {
                    let person_clone = person.clone();
                    let file_manager = self.file_manager.clone();
                    
                    Command::perform(
                        async move {
                            file_manager.delete_person(&person_clone).map_err(|e| e.to_string())
                        },
                        Message::PersonDeleted
                    )
                } else {
                    Command::none()
                }
            }
            
            Message::PersonDeleted(result) => {
                match result {
                    Ok(()) => {
                        if let Some(id) = self.selected_person {
                            // Store the person ID before removing
                            let person_id_to_remove = id;
                            self.persons.retain(|p| p.id != person_id_to_remove);
                            if self.selected_person == Some(person_id_to_remove) {
                                self.selected_person = None;
                                self.evidence_files.clear();
                            }
                            self.update_filtered_persons();
                            self.update_status("Person successfully deleted".to_string());
                        }
                    }
                    Err(e) => {
                        self.update_status(format!("Failed to delete person: {}", e));
                    }
                }
                Command::none()
            }
            
            Message::AddInfoTypeChanged(value) => {
                self.new_info_type = value;
                Command::none()
            }
            
            Message::AddInfoValueChanged(value) => {
                self.new_info_value = value;
                Command::none()
            }
            
            Message::AddInfoSubmitted => {
                if !self.new_info_type.trim().is_empty() && !self.new_info_value.trim().is_empty() {
                    if let Some(person_id) = self.selected_person {
                        if let Some(person) = self.persons.iter().find(|p| p.id == person_id) {
                            let person_clone = person.clone();
                            let info_type = self.new_info_type.trim().to_string();
                            let info_value = self.new_info_value.trim().to_string();
                            let file_manager = self.file_manager.clone();
                            
                            self.new_info_type.clear();
                            self.new_info_value.clear();
                            
                            Command::perform(
                                async move {
                                    let mut person = person_clone;
                                    person.add_information(info_type, info_value);
                                    file_manager.save_person_data(&person).map_err(|e| e.to_string())
                                },
                                Message::InfoAdded
                            )
                        } else {
                            Command::none()
                        }
                    } else {
                        Command::none()
                    }
                } else {
                    Command::none()
                }
            }
            
            Message::InfoAdded(result) => {
                match result {
                    Ok(()) => {
                        self.update_status("Information successfully added".to_string());
                        // Refresh the person data
                        if let Some(person_id) = self.selected_person {
                            if let Some(person) = self.persons.iter_mut().find(|p| p.id == person_id) {
                                // Reload person data to get updated information
                                if let Ok(updated_person) = self.file_manager.load_person_data(
                                    &self.file_manager.get_evidence_dir().join(person.folder_name())
                                ) {
                                    *person = updated_person;
                                }
                            }
                        }
                    }
                    Err(e) => {
                        self.update_status(format!("Failed to add information: {}", e));
                    }
                }
                Command::none()
            }
            
            Message::RemoveInfo(info_id) => {
                if let Some(person_id) = self.selected_person {
                    if let Some(person) = self.persons.iter().find(|p| p.id == person_id) {
                        let person_clone = person.clone();
                        let file_manager = self.file_manager.clone();
                        
                        Command::perform(
                            async move {
                                let mut person = person_clone;
                                person.remove_information(info_id);
                                file_manager.save_person_data(&person).map_err(|e| e.to_string())
                            },
                            Message::InfoRemoved
                        )
                    } else {
                        Command::none()
                    }
                } else {
                    Command::none()
                }
            }
            
            Message::InfoRemoved(result) => {
                match result {
                    Ok(()) => {
                        self.update_status("Information successfully removed".to_string());
                        // Refresh the person data
                        if let Some(person_id) = self.selected_person {
                            if let Some(person) = self.persons.iter_mut().find(|p| p.id == person_id) {
                                if let Ok(updated_person) = self.file_manager.load_person_data(
                                    &self.file_manager.get_evidence_dir().join(person.folder_name())
                                ) {
                                    *person = updated_person;
                                }
                            }
                        }
                    }
                    Err(e) => {
                        self.update_status(format!("Failed to remove information: {}", e));
                    }
                }
                Command::none()
            }
            
            Message::AddQuoteTextChanged(value) => {
                self.new_quote_text = value;
                Command::none()
            }
            
            Message::AddQuoteDateChanged(value) => {
                self.new_quote_date = value;
                Command::none()
            }
            
            Message::AddQuoteTimeChanged(value) => {
                self.new_quote_time = value;
                Command::none()
            }
            
            Message::AddQuotePlaceChanged(value) => {
                self.new_quote_place = value;
                Command::none()
            }
            
            Message::AddQuoteSubmitted => {
                if !self.new_quote_text.trim().is_empty() && !self.new_quote_date.trim().is_empty() {
                    if let Some(person_id) = self.selected_person {
                        if let Some(person) = self.persons.iter().find(|p| p.id == person_id) {
                            let person_clone = person.clone();
                            let quote_text = self.new_quote_text.trim().to_string();
                            let quote_date = self.new_quote_date.trim().to_string();
                            let quote_time = if self.new_quote_time.trim().is_empty() {
                                None
                            } else {
                                Some(self.new_quote_time.trim().to_string())
                            };
                            let quote_place = if self.new_quote_place.trim().is_empty() {
                                None
                            } else {
                                Some(self.new_quote_place.trim().to_string())
                            };
                            let file_manager = self.file_manager.clone();
                            
                            self.new_quote_text.clear();
                            self.new_quote_date.clear();
                            self.new_quote_time.clear();
                            self.new_quote_place.clear();
                            
                            Command::perform(
                                async move {
                                    let mut person = person_clone;
                                    person.add_quote(quote_text, quote_date, quote_time, quote_place);
                                    file_manager.save_person_data(&person).map_err(|e| e.to_string())
                                },
                                Message::QuoteAdded
                            )
                        } else {
                            Command::none()
                        }
                    } else {
                        Command::none()
                    }
                } else {
                    Command::none()
                }
            }
            
            Message::QuoteAdded(result) => {
                match result {
                    Ok(()) => {
                        self.update_status("Quote successfully added".to_string());
                        // Refresh the person data
                        if let Some(person_id) = self.selected_person {
                            if let Some(person) = self.persons.iter_mut().find(|p| p.id == person_id) {
                                if let Ok(updated_person) = self.file_manager.load_person_data(
                                    &self.file_manager.get_evidence_dir().join(person.folder_name())
                                ) {
                                    *person = updated_person;
                                }
                            }
                        }
                    }
                    Err(e) => {
                        self.update_status(format!("Failed to add quote: {}", e));
                    }
                }
                Command::none()
            }
            
            Message::RemoveQuote(quote_id) => {
                if let Some(person_id) = self.selected_person {
                    if let Some(person) = self.persons.iter().find(|p| p.id == person_id) {
                        let person_clone = person.clone();
                        let file_manager = self.file_manager.clone();
                        
                        Command::perform(
                            async move {
                                let mut person = person_clone;
                                person.remove_quote(quote_id);
                                file_manager.save_person_data(&person).map_err(|e| e.to_string())
                            },
                            Message::QuoteRemoved
                        )
                    } else {
                        Command::none()
                    }
                } else {
                    Command::none()
                }
            }
            
            Message::QuoteRemoved(result) => {
                match result {
                    Ok(()) => {
                        self.update_status("Quote successfully removed".to_string());
                        // Refresh the person data
                        if let Some(person_id) = self.selected_person {
                            if let Some(person) = self.persons.iter_mut().find(|p| p.id == person_id) {
                                if let Ok(updated_person) = self.file_manager.load_person_data(
                                    &self.file_manager.get_evidence_dir().join(person.folder_name())
                                ) {
                                    *person = updated_person;
                                }
                            }
                        }
                    }
                    Err(e) => {
                        self.update_status(format!("Failed to remove quote: {}", e));
                    }
                }
                Command::none()
            }
            
            Message::TabChanged(tab) => {
                self.current_tab = tab;
                Command::none()
            }
            
            Message::SelectFileClicked => {
                if let Some(_person_id) = self.selected_person {
                    Command::perform(
                        async {
                            rfd::FileDialog::new()
                                .add_filter("All Files", &["*"])
                                .add_filter("Images", &["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"])
                                .add_filter("Audio", &["mp3", "wav", "flac", "aac", "ogg", "m4a"])
                                .add_filter("Videos", &["mp4", "avi", "mov", "wmv", "flv", "webm", "mkv"])
                                .add_filter("Documents", &["pdf", "doc", "docx", "txt", "rtf"])
                                .pick_file()
                        },
                        |path| {
                            if let Some(path) = path {
                                Message::FileSelected(path)
                            } else {
                                Message::StatusMessage("File selection cancelled".to_string())
                            }
                        }
                    )
                } else {
                    Command::perform(
                        async { Message::StatusMessage("Please select a person before adding files".to_string()) },
                        |msg| msg
                    )
                }
            }
            
            Message::FileSelected(path) => {
                if let Some(person_id) = self.selected_person {
                    if let Some(person) = self.persons.iter().find(|p| p.id == person_id) {
                        let person_clone = person.clone();
                        let file_manager = self.file_manager.clone();
                        
                        Command::perform(
                            async move {
                                if let Some(extension) = path.extension() {
                                    let ext_str = extension.to_string_lossy();
                                    
                                    if let Some(evidence_type) = EvidenceType::from_extension(&ext_str) {
                                        file_manager.copy_file_to_evidence(&person_clone, &path, evidence_type).map_err(|e| e.to_string())
                                    } else {
                                        Err(format!("Unsupported file type: {}", ext_str))
                                    }
                                } else {
                                    Err("File has no extension".to_string())
                                }
                            },
                            |result| {
                                match result {
                                    Ok(_) => Message::FileAddedSuccessfully,
                                    Err(e) => Message::StatusMessage(format!("Failed to add file: {}", e)),
                                }
                            }
                        )
                    } else {
                        Command::none()
                    }
                } else {
                    Command::none()
                }
            }
            
            Message::FileAddedSuccessfully => {
                self.update_status("File successfully added".to_string());
                self.refresh_evidence_files();
                Command::none()
            }
            
            Message::ImportClicked => {
                Command::perform(
                    async {
                        rfd::FileDialog::new()
                            .add_filter("Evidence Manager Archive", &["ema"])
                            .pick_file()
                    },
                    |path| {
                        if let Some(path) = path {
                            Message::ImportFileSelected(path)
                        } else {
                            Message::ShowImportDialog(false)
                        }
                    }
                )
            }
            
            Message::ExportClicked => {
                Command::perform(
                    async {
                        rfd::FileDialog::new()
                            .add_filter("Evidence Manager Archive", &["ema"])
                            .set_file_name("evidence_export.ema")
                            .save_file()
                    },
                    |path| {
                        if let Some(path) = path {
                            Message::ExportFileSelected(path)
                        } else {
                            Message::ShowExportDialog(false)
                        }
                    }
                )
            }
            
            Message::ImportFileSelected(path) => {
                self.show_import_dialog = false;
                let export_import_manager = self.export_import_manager.clone();
                
                Command::perform(
                    async move {
                        export_import_manager.import_from_ema(&path, None).map_err(|e| e.to_string())
                    },
                    Message::ImportComplete
                )
            }
            
            Message::ExportFileSelected(path) => {
                self.show_export_dialog = false;
                let export_import_manager = self.export_import_manager.clone();
                let persons = self.persons.clone();
                
                Command::perform(
                    async move {
                        export_import_manager.export_to_ema(&path, &persons, None).map_err(|e| e.to_string())
                    },
                    Message::ExportComplete
                )
            }
            
            Message::ImportComplete(result) => {
                match result {
                    Ok(imported_persons) => {
                        self.persons.extend(imported_persons);
                        self.persons.sort_by(|a, b| a.name.cmp(&b.name));
                        self.update_filtered_persons();
                        self.update_status(".ema successfully imported".to_string());
                    }
                    Err(e) => {
                        self.update_status(format!("Failed to import evidence: {}", e));
                    }
                }
                Command::none()
            }
            
            Message::ExportComplete(result) => {
                match result {
                    Ok(()) => {
                        self.update_status(".ema successfully exported".to_string());
                    }
                    Err(e) => {
                        self.update_status(format!("Failed to export evidence: {}", e));
                    }
                }
                Command::none()
            }
            
            Message::SearchQueryChanged(query) => {
                self.search_query = query;
                self.update_filtered_persons();
                Command::none()
            }
            
            Message::ShowAddPersonDialog(show) => {
                self.show_add_person_dialog = show;
                if !show {
                    self.new_person_name.clear();
                }
                Command::none()
            }
            
            Message::ShowImportDialog(show) => {
                self.show_import_dialog = show;
                Command::none()
            }
            
            Message::ShowExportDialog(show) => {
                self.show_export_dialog = show;
                Command::none()
            }
            
            Message::StatusMessage(message) => {
                self.update_status(message);
                Command::none()
            }
            
        }
    }

    fn view(&self) -> Element<'_, Message> {
        crate::gui::view(self)
    }

    fn subscription(&self) -> Subscription<Message> {
        Subscription::none()
    }
}