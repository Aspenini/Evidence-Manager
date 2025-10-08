use crate::models::{Person, EvidenceFile, EvidenceType};
use crate::file_manager::FileManager;
use crate::export_import::ExportImportManager;
use eframe::egui;
use std::path::PathBuf;
use uuid::Uuid;

#[derive(Debug, Clone, PartialEq)]
pub enum EvidenceTab {
    Information,
    Images,
    Audio,
    Videos,
    Documents,
    Quotes,
}

pub struct EvidenceManagerApp {
    file_manager: FileManager,
    export_import_manager: ExportImportManager,
    persons: Vec<Person>,
    selected_person: Option<Uuid>,
    evidence_files: Vec<EvidenceFile>,
    
    // UI State
    show_add_person_dialog: bool,
    show_edit_person_dialog: bool,
    show_export_dialog: bool,
    show_import_dialog: bool,
    current_tab: EvidenceTab,
    
    // Search
    search_query: String,
    filtered_persons: Vec<Uuid>,
    
    // Add/Edit person fields
    new_person_name: String,
    
    // Add information fields
    new_info_type: String,
    new_info_value: String,
    
    // Add quote fields
    new_quote_text: String,
    new_quote_date: String,
    new_quote_time: String,
    new_quote_place: String,
    
    // File operations
    pending_file_drops: Vec<PathBuf>,
    
    // Status
    status_message: String,
    status_timeout: f32,
    progress_message: String,
    progress_value: f32,
    show_progress: bool,
}

impl EvidenceManagerApp {
    pub fn new() -> Self {
        let file_manager = FileManager::new().unwrap_or_else(|e| {
            eprintln!("Failed to initialize file manager: {}", e);
            std::process::exit(1);
        });
        
        let export_import_manager = ExportImportManager::new(file_manager.clone());
        let persons = file_manager.load_all_persons().unwrap_or_default();
        
        Self {
            file_manager,
            export_import_manager,
            persons,
            selected_person: None,
            evidence_files: Vec::new(),
            
            show_add_person_dialog: false,
            show_edit_person_dialog: false,
            show_export_dialog: false,
            show_import_dialog: false,
            current_tab: EvidenceTab::Information,
            
            search_query: String::new(),
            filtered_persons: Vec::new(),
            
            new_person_name: String::new(),
            
            new_info_type: String::new(),
            new_info_value: String::new(),
            
            new_quote_text: String::new(),
            new_quote_date: String::new(),
            new_quote_time: String::new(),
            new_quote_place: String::new(),
            
            pending_file_drops: Vec::new(),
            
            status_message: String::new(),
            status_timeout: 0.0,
            progress_message: String::new(),
            progress_value: 0.0,
            show_progress: false,
        }
    }

    fn update_status(&mut self, message: String) {
        self.status_message = message;
        self.status_timeout = 5.0; // Show for 5 seconds
        self.show_progress = false;
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

    fn add_information_to_person(&mut self) {
        if !self.new_info_type.trim().is_empty() && !self.new_info_value.trim().is_empty() {
            if let Some(person_id) = self.selected_person {
                if let Some(person) = self.persons.iter_mut().find(|p| p.id == person_id) {
                    person.add_information(self.new_info_type.trim().to_string(), self.new_info_value.trim().to_string());
                    
                    if let Err(e) = self.file_manager.save_person_data(person) {
                        self.update_status(format!("Failed to save person: {}", e));
                    } else {
                        self.update_status("Information successfully added".to_string());
                    }
                }
            }
            
            self.new_info_type.clear();
            self.new_info_value.clear();
        }
    }

    fn remove_information_from_person(&mut self, info_id: Uuid) {
        if let Some(person_id) = self.selected_person {
            if let Some(person) = self.persons.iter_mut().find(|p| p.id == person_id) {
                person.remove_information(info_id);
                
                if let Err(e) = self.file_manager.save_person_data(person) {
                    self.update_status(format!("Failed to save person: {}", e));
                } else {
                    self.update_status("Information successfully removed".to_string());
                }
            }
        }
    }

    fn add_quote_to_person(&mut self) {
        if !self.new_quote_text.trim().is_empty() && !self.new_quote_date.trim().is_empty() {
            if let Some(person_id) = self.selected_person {
                if let Some(person) = self.persons.iter_mut().find(|p| p.id == person_id) {
                    let time = if self.new_quote_time.trim().is_empty() {
                        None
                    } else {
                        Some(self.new_quote_time.trim().to_string())
                    };
                    
                    let place = if self.new_quote_place.trim().is_empty() {
                        None
                    } else {
                        Some(self.new_quote_place.trim().to_string())
                    };
                    
                    person.add_quote(
                        self.new_quote_text.trim().to_string(),
                        self.new_quote_date.trim().to_string(),
                        time,
                        place
                    );
                    
                    if let Err(e) = self.file_manager.save_person_data(person) {
                        self.update_status(format!("Failed to save person: {}", e));
                    } else {
                        self.update_status("Quote successfully added".to_string());
                    }
                }
            }
            
            self.new_quote_text.clear();
            self.new_quote_date.clear();
            self.new_quote_time.clear();
            self.new_quote_place.clear();
        }
    }

    fn remove_quote_from_person(&mut self, quote_id: Uuid) {
        if let Some(person_id) = self.selected_person {
            if let Some(person) = self.persons.iter_mut().find(|p| p.id == person_id) {
                person.remove_quote(quote_id);
                
                if let Err(e) = self.file_manager.save_person_data(person) {
                    self.update_status(format!("Failed to save person: {}", e));
                } else {
                    self.update_status("Quote successfully removed".to_string());
                }
            }
        }
    }

    fn handle_file_drops(&mut self, ctx: &egui::Context) {
        if !ctx.input(|i| i.raw.dropped_files.is_empty()) {
            let dropped_files: Vec<PathBuf> = ctx.input(|i| {
                i.raw.dropped_files
                    .iter()
                    .filter_map(|f| f.path.clone())
                    .collect()
            });
            
            // Check if any dropped files are .ema files
            for file_path in dropped_files {
                if let Some(extension) = file_path.extension() {
                    if extension.to_string_lossy().to_lowercase() == "ema" {
                        // Handle .ema import
                        let progress_callback = Box::new(|_msg: String| {
                            // Progress callback for drag-and-drop import
                        });
                        
                        match self.export_import_manager.import_from_ema(&file_path, Some(progress_callback)) {
                            Ok(imported_persons) => {
                                self.persons.extend(imported_persons);
                                self.persons.sort_by(|a, b| a.name.cmp(&b.name));
                                self.update_status(format!("Successfully imported evidence from {:?}", file_path));
                            }
                            Err(e) => {
                                self.update_status(format!("Failed to import evidence: {}", e));
                            }
                        }
                        continue;
                    }
                }
                
                // Add to pending file drops for regular evidence files
                self.pending_file_drops.push(file_path);
            }
        }
    }

    fn process_pending_file_drops(&mut self) {
        if self.pending_file_drops.is_empty() {
            return;
        }

        if let Some(person_id) = self.selected_person {
            if let Some(person) = self.persons.iter().find(|p| p.id == person_id) {
                let person_clone = person.clone();
                let mut status_messages = Vec::new();
                let mut should_refresh = false;
                
                for file_path in self.pending_file_drops.drain(..) {
                    if let Some(extension) = file_path.extension() {
                        if let Some(evidence_type) = EvidenceType::from_extension(extension.to_string_lossy().as_ref()) {
                            match self.file_manager.copy_file_to_evidence(&person_clone, &file_path, evidence_type) {
                                Ok(_) => {
                                    status_messages.push(format!("Added {} to {}", 
                                        file_path.file_name().unwrap_or_default().to_string_lossy(),
                                        person_clone.name));
                                    should_refresh = true;
                                }
                                Err(e) => {
                                    status_messages.push(format!("Failed to add file: {}", e));
                                }
                            }
                        } else {
                            status_messages.push(format!("Unsupported file type: {}", 
                                file_path.file_name().unwrap_or_default().to_string_lossy()));
                        }
                    }
                }
                
                if let Some(msg) = status_messages.last() {
                    self.update_status(msg.clone());
                }
                
                if should_refresh {
                    self.refresh_evidence_files();
                }
            }
        } else {
            self.update_status("Please select a person before dropping files".to_string());
            self.pending_file_drops.clear();
        }
    }

    fn refresh_evidence_files(&mut self) {
        if let Some(person_id) = self.selected_person {
            if let Some(person) = self.persons.iter().find(|p| p.id == person_id) {
                self.evidence_files = self.file_manager.scan_person_evidence(person).unwrap_or_default();
            }
        } else {
            self.evidence_files.clear();
        }
    }

    fn add_person(&mut self) {
        if !self.new_person_name.trim().is_empty() {
            let person = Person::new(self.new_person_name.trim().to_string());

            if let Err(e) = self.file_manager.save_person_data(&person) {
                self.update_status(format!("Failed to save person: {}", e));
                return;
            }

            self.persons.push(person);
            self.persons.sort_by(|a, b| a.name.cmp(&b.name));
            
            self.new_person_name.clear();
            self.show_add_person_dialog = false;
            
                    self.update_status("Person successfully added".to_string());
        }
    }

    fn delete_person(&mut self, person: &Person) {
        if let Err(e) = self.file_manager.delete_person(person) {
            self.update_status(format!("Failed to delete person: {}", e));
            return;
        }

        self.persons.retain(|p| p.id != person.id);
        
        if self.selected_person == Some(person.id) {
            self.selected_person = None;
            self.evidence_files.clear();
        }
        
        self.update_status("Person successfully deleted".to_string());
    }
}

impl eframe::App for EvidenceManagerApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        self.handle_file_drops(ctx);
        self.process_pending_file_drops();
        self.update_filtered_persons();

        // Update status timeout
        if self.status_timeout > 0.0 {
            self.status_timeout -= ctx.input(|i| i.unstable_dt);
        }

        // Left panel - Person list
        egui::SidePanel::left("person_list")
            .resizable(true)
            .default_width(300.0)
            .show(ctx, |ui| {
                // Simple stacked buttons
                if ui.button("+ Add Person").clicked() {
                    self.show_add_person_dialog = true;
                }
                
                if ui.button("Import .ema").clicked() {
                    self.show_import_dialog = true;
                }
                
                if ui.button("Export All").clicked() {
                    self.show_export_dialog = true;
                }
                
                if ui.button("Check Updates").clicked() {
                    self.update_status("No updates available".to_string());
                }
                
                ui.separator();
                
                ui.heading("People");
                
                // Search bar
                ui.text_edit_singleline(&mut self.search_query);
                
                // Person list
                egui::ScrollArea::vertical().show(ui, |ui| {
                    let filtered_ids = self.filtered_persons.clone();
                    for person_id in filtered_ids {
                        if let Some(person) = self.persons.iter().find(|p| p.id == person_id) {
                            let is_selected = self.selected_person == Some(person.id);
                            let person_name = person.name.clone();
                            let person_id_copy = person.id;
                            
                            ui.horizontal(|ui| {
                                let response = ui.add_sized([ui.available_width(), 0.0], 
                                    egui::Button::new(&person_name).selected(is_selected));
                                
                                if response.clicked() {
                                    self.selected_person = Some(person_id_copy);
                                    self.refresh_evidence_files();
                                }
                            });
                        }
                    }
                });
            });

        // Right panel - Evidence files
        egui::CentralPanel::default().show(ctx, |ui| {
            if let Some(person_id) = self.selected_person {
                if let Some(person) = self.persons.iter().find(|p| p.id == person_id) {
                    let person_clone = person.clone();
                    ui.horizontal(|ui| {
                        ui.heading(format!("Evidence for: {}", person_clone.name));
                        
                        ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                            if ui.button("Delete Person").clicked() {
                                self.delete_person(&person_clone);
                            }
                            
                            if ui.button("Export Evidence").clicked() {
                                // Export just this person's evidence
                                self.update_status("Export single person not yet implemented".to_string());
                            }
                        });
                    });
                    
                    ui.separator();
                    
                    // Tabs
                    ui.horizontal(|ui| {
                        ui.selectable_value(&mut self.current_tab, EvidenceTab::Information, "Information");
                        ui.selectable_value(&mut self.current_tab, EvidenceTab::Images, "Images");
                        ui.selectable_value(&mut self.current_tab, EvidenceTab::Audio, "Audio");
                        ui.selectable_value(&mut self.current_tab, EvidenceTab::Videos, "Videos");
                        ui.selectable_value(&mut self.current_tab, EvidenceTab::Documents, "Documents");
                        ui.selectable_value(&mut self.current_tab, EvidenceTab::Quotes, "Quotes");
                    });
                    
                    ui.separator();
                    
                    match self.current_tab {
                        EvidenceTab::Information => {
                            self.show_information_tab(ui);
                        }
                        EvidenceTab::Images => {
                            self.show_media_tab(ui, EvidenceType::Image);
                        }
                        EvidenceTab::Audio => {
                            self.show_media_tab(ui, EvidenceType::Audio);
                        }
                        EvidenceTab::Videos => {
                            self.show_media_tab(ui, EvidenceType::Video);
                        }
                        EvidenceTab::Documents => {
                            self.show_media_tab(ui, EvidenceType::Document);
                        }
                        EvidenceTab::Quotes => {
                            self.show_quotes_tab(ui);
                        }
                    }
                }
            } else {
                ui.heading("Select a person to view evidence");
                ui.label("Drag and drop files onto the application to add evidence");
            }
        });

        // Dialogs
        self.show_add_person_dialog(ctx);
        self.show_edit_person_dialog(ctx);
        self.show_export_dialog(ctx);
        self.show_import_dialog(ctx);

        // Footer with status and progress
        egui::TopBottomPanel::bottom("footer").show(ctx, |ui| {
            ui.horizontal(|ui| {
                // Status message
                if !self.status_message.is_empty() && self.status_timeout > 0.0 {
                    ui.label(&self.status_message);
                }
                
                // Progress bar
                if self.show_progress {
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        ui.label(&self.progress_message);
                        ui.add(egui::ProgressBar::new(self.progress_value / 100.0));
                    });
                }
            });
        });
    }
}

impl EvidenceManagerApp {
    fn show_add_person_dialog(&mut self, ctx: &egui::Context) {
        if !self.show_add_person_dialog {
            return;
        }

        let mut should_close = false;
        let mut should_add = false;
        
        egui::Window::new("Add Person")
            .open(&mut self.show_add_person_dialog)
            .show(ctx, |ui| {
                ui.label("Name:");
                ui.text_edit_singleline(&mut self.new_person_name);
                
                ui.horizontal(|ui| {
                    if ui.button("Cancel").clicked() {
                        should_close = true;
                    }
                    
                    if ui.button("Add").clicked() {
                        should_add = true;
                        should_close = true;
                    }
                });
            });
            
        if should_close {
            self.show_add_person_dialog = false;
            if should_add {
                self.add_person();
            } else {
                self.new_person_name.clear();
            }
        }
    }

    fn show_edit_person_dialog(&mut self, ctx: &egui::Context) {
        if !self.show_edit_person_dialog {
            return;
        }

        let mut should_close = false;
        let mut should_save = false;
        
        egui::Window::new("Edit Person")
            .open(&mut self.show_edit_person_dialog)
            .show(ctx, |ui| {
                ui.label("Name:");
                ui.text_edit_singleline(&mut self.new_person_name);
                
                ui.horizontal(|ui| {
                    if ui.button("Cancel").clicked() {
                        should_close = true;
                    }
                    
                    if ui.button("Save").clicked() {
                        should_save = true;
                        should_close = true;
                    }
                });
            });
            
        if should_close {
            self.show_edit_person_dialog = false;
            
            if should_save {
                if let Some(person_id) = self.selected_person {
                    if let Some(person) = self.persons.iter_mut().find(|p| p.id == person_id) {
                        person.name = self.new_person_name.trim().to_string();
                        person.update_timestamp();
                        
                        if let Err(e) = self.file_manager.save_person_data(person) {
                            self.update_status(format!("Failed to save person: {}", e));
                        } else {
                            self.update_status("Person updated successfully".to_string());
                        }
                    }
                }
            }
        }
    }

    fn show_export_dialog(&mut self, _ctx: &egui::Context) {
        if !self.show_export_dialog {
            return;
        }

        self.show_export_dialog = false;
        
        if let Some(path) = rfd::FileDialog::new()
            .add_filter("Evidence Manager Archive", &["ema"])
            .set_file_name("evidence_export.ema")
            .save_file()
        {
            let progress_callback = Box::new(|_msg: String| {
                // This is a simplified callback - in a real implementation you'd need
                // to handle this differently due to borrowing constraints
            });
            
            match self.export_import_manager.export_to_ema(&path, &self.persons, Some(progress_callback)) {
                Ok(_) => {
                    self.update_status(".ema successfully exported".to_string());
                }
                Err(e) => {
                    self.update_status(format!("Failed to export evidence: {}", e));
                }
            }
        }
    }

    fn show_import_dialog(&mut self, _ctx: &egui::Context) {
        if !self.show_import_dialog {
            return;
        }

        self.show_import_dialog = false;
        
        if let Some(path) = rfd::FileDialog::new()
            .add_filter("Evidence Manager Archive", &["ema"])
            .pick_file()
        {
            let progress_callback = Box::new(|_msg: String| {
                // This is a simplified callback - in a real implementation you'd need
                // to handle this differently due to borrowing constraints
            });
            
            match self.export_import_manager.import_from_ema(&path, Some(progress_callback)) {
                Ok(imported_persons) => {
                    self.persons.extend(imported_persons);
                    self.persons.sort_by(|a, b| a.name.cmp(&b.name));
                    self.update_status(".ema successfully imported".to_string());
                }
                Err(e) => {
                    self.update_status(format!("Failed to import evidence: {}", e));
                }
            }
        }
    }

    fn show_information_tab(&mut self, ui: &mut egui::Ui) {
        ui.label("Add Info Section:");
        
        ui.horizontal(|ui| {
            ui.label("Info Type:");
            ui.text_edit_singleline(&mut self.new_info_type);
        });
        
        ui.horizontal(|ui| {
            ui.label("Value:");
            ui.text_edit_singleline(&mut self.new_info_value);
        });
        
        if ui.button("Add Info").clicked() {
            self.add_information_to_person();
        }
        
        ui.separator();
        
        // Information table with proper columns
        if let Some(person_id) = self.selected_person {
            if let Some(person) = self.persons.iter().find(|p| p.id == person_id) {
                let person_clone = person.clone();
                
                // Create table header
                ui.horizontal(|ui| {
                    ui.strong("Type");
                    ui.separator();
                    ui.strong("Value");
                    ui.separator();
                    ui.strong("Actions");
                });
                
                ui.separator();
                
                egui::ScrollArea::vertical().show(ui, |ui| {
                    for info in &person_clone.information {
                        let info_id = info.id;
                        ui.horizontal(|ui| {
                            // Type column
                            ui.label(&info.info_type);
                            ui.separator();
                            
                            // Value column
                            ui.label(&info.value);
                            ui.separator();
                            
                            // Actions column
                            if ui.button("Delete").clicked() {
                                self.remove_information_from_person(info_id);
                            }
                        });
                    }
                });
            }
        }
    }

    fn show_media_tab(&mut self, ui: &mut egui::Ui, media_type: EvidenceType) {
        ui.label(format!("{} Files:", match media_type {
            EvidenceType::Image => "Image",
            EvidenceType::Audio => "Audio", 
            EvidenceType::Video => "Video",
            EvidenceType::Document => "Document",
            EvidenceType::Quote => "Quote",
        }));
        
        ui.label("Drop files here to add evidence");
        
        egui::ScrollArea::vertical().show(ui, |ui| {
            for evidence_file in &self.evidence_files {
                if evidence_file.file_type == media_type {
                    ui.horizontal(|ui| {
                        let icon = match evidence_file.file_type {
                            EvidenceType::Image => "🖼",
                            EvidenceType::Audio => "🎵",
                            EvidenceType::Video => "🎬",
                            EvidenceType::Document => "📄",
                            EvidenceType::Quote => "💬",
                        };
                        
                        ui.label(icon);
                        ui.label(&evidence_file.original_name);
                        ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                            ui.label(format!("{} KB", evidence_file.size / 1024));
                        });
                    });
                }
            }
        });
    }

    fn show_quotes_tab(&mut self, ui: &mut egui::Ui) {
        ui.label("Add Quote Section:");
        
        ui.horizontal(|ui| {
            ui.label("Quote:");
            ui.text_edit_singleline(&mut self.new_quote_text);
        });
        
        ui.horizontal(|ui| {
            ui.label("Date:");
            ui.text_edit_singleline(&mut self.new_quote_date);
        });
        
        ui.horizontal(|ui| {
            ui.label("Time (optional):");
            ui.text_edit_singleline(&mut self.new_quote_time);
        });
        
        ui.horizontal(|ui| {
            ui.label("Place (optional):");
            ui.text_edit_singleline(&mut self.new_quote_place);
        });
        
        if ui.button("Add Quote").clicked() {
            self.add_quote_to_person();
        }
        
        ui.separator();
        
        // Quotes table
        if let Some(person_id) = self.selected_person {
            if let Some(person) = self.persons.iter().find(|p| p.id == person_id) {
                let person_clone = person.clone();
                
                // Create table header
                ui.horizontal(|ui| {
                    ui.strong("Quote");
                    ui.separator();
                    ui.strong("Date");
                    ui.separator();
                    ui.strong("Time");
                    ui.separator();
                    ui.strong("Place");
                    ui.separator();
                    ui.strong("Actions");
                });
                
                ui.separator();
                
                egui::ScrollArea::vertical().show(ui, |ui| {
                    for quote in &person_clone.quotes {
                        let quote_id = quote.id;
                        ui.horizontal(|ui| {
                            // Quote column
                            ui.label(&quote.quote);
                            ui.separator();
                            
                            // Date column
                            ui.label(&quote.date);
                            ui.separator();
                            
                            // Time column
                            ui.label(quote.time.as_deref().unwrap_or("-"));
                            ui.separator();
                            
                            // Place column
                            ui.label(quote.place.as_deref().unwrap_or("-"));
                            ui.separator();
                            
                            // Actions column
                            if ui.button("Delete").clicked() {
                                self.remove_quote_from_person(quote_id);
                            }
                        });
                    }
                });
            }
        }
    }
}
