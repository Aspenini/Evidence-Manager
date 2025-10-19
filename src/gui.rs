use crate::models::{Person, EvidenceFile, EvidenceType};
use crate::state::{AppState, Message};
use iced::{
    widget::{
        button, column, container, row, scrollable, text, text_input, 
        Column, Row, Space,
    },
    Element, Length, Alignment, Color, theme,
};

#[derive(Debug, Clone, PartialEq)]
pub enum EvidenceTab {
    Information,
    Images,
    Audio,
    Videos,
    Documents,
    Quotes,
}

impl EvidenceTab {
    fn all() -> Vec<EvidenceTab> {
        vec![
            EvidenceTab::Information,
            EvidenceTab::Images,
            EvidenceTab::Audio,
            EvidenceTab::Videos,
            EvidenceTab::Documents,
            EvidenceTab::Quotes,
        ]
    }
    
    fn label(&self) -> &'static str {
        match self {
            EvidenceTab::Information => "Information",
            EvidenceTab::Images => "Images",
            EvidenceTab::Audio => "Audio",
            EvidenceTab::Videos => "Videos",
            EvidenceTab::Documents => "Documents",
            EvidenceTab::Quotes => "Quotes",
        }
    }
}

pub fn view(state: &AppState) -> Element<'_, Message> {
    let content = row![
        // Left sidebar
        sidebar(state),
        // Main content
        main_content(state),
    ]
    .spacing(10)
    .padding(10);

    let mut layout = column![content];

    // Add modal dialogs
    if state.show_add_person_dialog {
        layout = layout.push(add_person_dialog(state).unwrap());
    }

    // Add status bar at bottom
    if !state.status_message.is_empty() {
        layout = layout.push(
            container(
                text(&state.status_message)
                    .style(theme::Text::Color(Color::from_rgb(0.0, 0.5, 0.0)))
            )
            .padding(5)
            .style(theme::Container::Box)
        );
    }

    layout.into()
}

fn sidebar(state: &AppState) -> Element<'_, Message> {
    let mut sidebar_content = column![
        text("Evidence Manager").size(20).style(theme::Text::Color(Color::from_rgb(0.2, 0.2, 0.8))),
        Space::with_height(10),
    ];

    // Action buttons
    sidebar_content = sidebar_content.push(
        column![
            button("+ Add Person")
                .on_press(Message::AddPersonClicked)
                .style(theme::Button::Primary),
            button("Import .ema")
                .on_press(Message::ImportClicked),
            button("Export All")
                .on_press(Message::ExportClicked),
            button("Check Updates")
                .on_press(Message::StatusMessage("No updates available".to_string())),
        ]
        .spacing(5)
    );

    sidebar_content = sidebar_content.push(Space::with_height(10));
    sidebar_content = sidebar_content.push(text("People").size(16));

    // Search bar
    sidebar_content = sidebar_content.push(
        text_input("Search people...", &state.search_query)
            .on_input(Message::SearchQueryChanged)
    );

    // Person list
    let person_list: Element<Message> = if state.filtered_persons.is_empty() {
        text("No people found").style(theme::Text::Color(Color::from_rgb(0.5, 0.5, 0.5))).into()
    } else {
        let mut person_buttons = Column::new().spacing(2);
        
        for person_id in &state.filtered_persons {
            if let Some(person) = state.persons.iter().find(|p| p.id == *person_id) {
                let is_selected = state.selected_person == Some(person.id);
                let button_style = if is_selected {
                    theme::Button::Primary
                } else {
                    theme::Button::Secondary
                };
                
                person_buttons = person_buttons.push(
                    button(&*person.name)
                        .on_press(Message::PersonSelected(person.id))
                        .style(button_style)
                        .width(Length::Fill)
                );
            }
        }
        
        scrollable(person_buttons)
            .height(Length::Fill)
            .into()
    };

    sidebar_content = sidebar_content.push(person_list);

    container(sidebar_content)
        .width(Length::Fixed(300.0))
        .height(Length::Fill)
        .padding(10)
        .style(theme::Container::Box)
        .into()
}

fn main_content(state: &AppState) -> Element<'_, Message> {
    if let Some(person_id) = state.selected_person {
        if let Some(person) = state.persons.iter().find(|p| p.id == person_id) {
            let mut content = column![
                // Header with person name and actions
                row![
                    text(format!("Evidence for: {}", person.name))
                        .size(18)
                        .style(theme::Text::Color(Color::from_rgb(0.2, 0.2, 0.8))),
                    Space::with_width(Length::Fill),
                    button("Delete Person")
                        .on_press(Message::DeletePerson(person.id))
                        .style(theme::Button::Destructive),
                    button("Export Evidence")
                        .on_press(Message::ExportPersonClicked),
                ]
                .spacing(10)
                .align_items(Alignment::Center),
                
                Space::with_height(10),
            ];

            // Tab navigation
            let mut tab_row = Row::new().spacing(5);
            for tab in EvidenceTab::all() {
                let is_selected = state.current_tab == tab;
                let button_style = if is_selected {
                    theme::Button::Primary
                } else {
                    theme::Button::Secondary
                };
                
                tab_row = tab_row.push(
                    button(tab.label())
                        .on_press(Message::TabChanged(tab.clone()))
                        .style(button_style)
                );
            }
            content = content.push(tab_row);
            content = content.push(Space::with_height(10));

            // Tab content
            match state.current_tab {
                EvidenceTab::Information => {
                    content = content.push(information_tab(state, person));
                }
                EvidenceTab::Images => {
                    content = content.push(media_tab(state, EvidenceType::Image));
                }
                EvidenceTab::Audio => {
                    content = content.push(media_tab(state, EvidenceType::Audio));
                }
                EvidenceTab::Videos => {
                    content = content.push(media_tab(state, EvidenceType::Video));
                }
                EvidenceTab::Documents => {
                    content = content.push(media_tab(state, EvidenceType::Document));
                }
                EvidenceTab::Quotes => {
                    content = content.push(quotes_tab(state, person));
                }
            }

            container(content)
                .width(Length::Fill)
                .height(Length::Fill)
                .padding(10)
                .style(theme::Container::Box)
                .into()
        } else {
            container(
                text("Person not found")
                    .style(theme::Text::Color(Color::from_rgb(0.8, 0.2, 0.2)))
            )
            .width(Length::Fill)
            .height(Length::Fill)
            .padding(20)
            .into()
        }
    } else {
        container(
            column![
                text("Select a person to view evidence")
                    .size(16)
                    .style(theme::Text::Color(Color::from_rgb(0.5, 0.5, 0.5))),
                Space::with_height(10),
                text("Use the 'Select File to Add' button in each tab to add evidence files")
                    .style(theme::Text::Color(Color::from_rgb(0.5, 0.5, 0.5))),
            ]
            .align_items(Alignment::Center)
        )
        .width(Length::Fill)
        .height(Length::Fill)
        .padding(20)
        .into()
    }
}

fn information_tab<'a>(state: &'a AppState, person: &'a Person) -> Element<'a, Message> {
    let mut content = column![
        text("Add Information").size(16),
        Space::with_height(5),
    ];

    // Add information form
    content = content.push(
        row![
            text_input("Info Type", &state.new_info_type)
                .on_input(Message::AddInfoTypeChanged),
            text_input("Value", &state.new_info_value)
                .on_input(Message::AddInfoValueChanged),
            button("Add Info")
                .on_press(Message::AddInfoSubmitted)
                .style(theme::Button::Primary),
        ]
        .spacing(5)
    );

    content = content.push(Space::with_height(10));

    // Information table
    if person.information.is_empty() {
        content = content.push(
            text("No information added yet")
                .style(theme::Text::Color(Color::from_rgb(0.5, 0.5, 0.5)))
        );
    } else {
        content = content.push(
            text("Information")
                .size(14)
                .style(theme::Text::Color(Color::from_rgb(0.2, 0.2, 0.8)))
        );

        let mut info_list = Column::new().spacing(2);
        for info in &person.information {
            info_list = info_list.push(
                row![
                    text(&info.info_type)
                        .width(Length::FillPortion(1)),
                    text(&info.value)
                        .width(Length::FillPortion(2)),
                    button("Delete")
                        .on_press(Message::RemoveInfo(info.id))
                        .style(theme::Button::Destructive),
                ]
                .spacing(5)
                .align_items(Alignment::Center)
            );
        }
        
        content = content.push(
            scrollable(info_list)
                .height(Length::Fixed(300.0))
        );
    }

    container(content)
        .width(Length::Fill)
        .padding(10)
        .into()
}

fn media_tab(state: &AppState, media_type: EvidenceType) -> Element<'_, Message> {
    let type_label = match media_type {
        EvidenceType::Image => "Image",
        EvidenceType::Audio => "Audio",
        EvidenceType::Video => "Video",
        EvidenceType::Document => "Document",
        EvidenceType::Quote => "Quote",
    };

    let mut content = column![
        text(format!("{} Files", type_label)).size(16),
        Space::with_height(5),
        button("Select File to Add")
            .on_press(Message::SelectFileClicked)
            .style(theme::Button::Primary),
        Space::with_height(10),
    ];

    let filtered_files: Vec<&EvidenceFile> = state.evidence_files
        .iter()
        .filter(|f| f.file_type == media_type)
        .collect();

    if filtered_files.is_empty() {
        content = content.push(
            text(format!("No {} files found", type_label.to_lowercase()))
                .style(theme::Text::Color(Color::from_rgb(0.5, 0.5, 0.5)))
        );
    } else {
        let mut file_list = Column::new().spacing(2);
        for file in filtered_files {
            let icon = match file.file_type {
                EvidenceType::Image => "🖼",
                EvidenceType::Audio => "🎵",
                EvidenceType::Video => "🎬",
                EvidenceType::Document => "📄",
                EvidenceType::Quote => "💬",
            };
            
            file_list = file_list.push(
                row![
                    text(icon),
                    text(&file.original_name)
                        .width(Length::Fill),
                    text(format!("{} KB", file.size / 1024))
                        .style(theme::Text::Color(Color::from_rgb(0.5, 0.5, 0.5))),
                ]
                .spacing(5)
                .align_items(Alignment::Center)
            );
        }
        
        content = content.push(
            scrollable(file_list)
                .height(Length::Fixed(400.0))
        );
    }

    container(content)
        .width(Length::Fill)
        .padding(10)
        .into()
}

fn quotes_tab<'a>(state: &'a AppState, person: &'a Person) -> Element<'a, Message> {
    let mut content = column![
        text("Add Quote").size(16),
        Space::with_height(5),
    ];

    // Add quote form
    content = content.push(
        column![
            text_input("Quote", &state.new_quote_text)
                .on_input(Message::AddQuoteTextChanged),
            text_input("Date", &state.new_quote_date)
                .on_input(Message::AddQuoteDateChanged),
            row![
                text_input("Time (optional)", &state.new_quote_time)
                    .on_input(Message::AddQuoteTimeChanged),
                text_input("Place (optional)", &state.new_quote_place)
                    .on_input(Message::AddQuotePlaceChanged),
            ]
            .spacing(5),
            button("Add Quote")
                .on_press(Message::AddQuoteSubmitted)
                .style(theme::Button::Primary),
        ]
        .spacing(5)
    );

    content = content.push(Space::with_height(10));

    // Quotes table
    if person.quotes.is_empty() {
        content = content.push(
            text("No quotes added yet")
                .style(theme::Text::Color(Color::from_rgb(0.5, 0.5, 0.5)))
        );
    } else {
        content = content.push(
            text("Quotes")
                .size(14)
                .style(theme::Text::Color(Color::from_rgb(0.2, 0.2, 0.8)))
        );

        let mut quote_list = Column::new().spacing(2);
        for quote in &person.quotes {
            quote_list = quote_list.push(
                row![
                    text(&quote.quote)
                        .width(Length::FillPortion(2)),
                    text(&quote.date)
                        .width(Length::FillPortion(1)),
                    text(quote.time.as_deref().unwrap_or("-"))
                        .width(Length::FillPortion(1)),
                    text(quote.place.as_deref().unwrap_or("-"))
                        .width(Length::FillPortion(1)),
                    button("Delete")
                        .on_press(Message::RemoveQuote(quote.id))
                        .style(theme::Button::Destructive),
                ]
                .spacing(5)
                .align_items(Alignment::Center)
            );
        }
        
        content = content.push(
            scrollable(quote_list)
                .height(Length::Fixed(300.0))
        );
    }

    container(content)
        .width(Length::Fill)
        .padding(10)
        .into()
}

// Modal dialogs
pub fn add_person_dialog(state: &AppState) -> Option<Element<'_, Message>> {
    if !state.show_add_person_dialog {
        return None;
    }

    Some(
        container(
            column![
                text("Add Person").size(18),
                Space::with_height(10),
                text_input("Name", &state.new_person_name)
                    .on_input(Message::AddPersonNameChanged),
                Space::with_height(10),
                row![
                    button("Cancel")
                        .on_press(Message::ShowAddPersonDialog(false)),
                    Space::with_width(Length::Fill),
                    button("Add")
                        .on_press(Message::AddPersonSubmitted)
                        .style(theme::Button::Primary),
                ]
                .spacing(10),
            ]
            .spacing(5)
        )
        .padding(20)
        .style(theme::Container::Box)
        .into()
    )
}