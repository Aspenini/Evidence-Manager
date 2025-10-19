mod models;
mod file_manager;
mod export_import;
mod state;
mod gui;

use iced::{Application, Settings};
use state::AppState;

fn main() -> iced::Result {
    AppState::run(Settings {
        window: iced::window::Settings {
            size: iced::Size::new(1200.0, 800.0),
            min_size: Some(iced::Size::new(800.0, 600.0)),
            ..Default::default()
        },
        ..Default::default()
    })
}
