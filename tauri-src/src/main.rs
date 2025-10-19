#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod app_state;
mod commands;
mod export_import;
mod file_manager;
mod models;

use app_state::AppState;

fn main() {
    let state = AppState::new().expect("failed to initialize application state");

    tauri::Builder::default()
        .manage(state)
        .invoke_handler(tauri::generate_handler![
            commands::list_persons,
            commands::add_person,
            commands::delete_person,
            commands::add_information,
            commands::remove_information,
            commands::add_quote,
            commands::remove_quote,
            commands::export_archive,
            commands::import_archive,
            commands::scan_evidence,
            commands::add_evidence,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
