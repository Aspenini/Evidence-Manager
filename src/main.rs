mod app;
mod models;
mod file_manager;
mod export_import;

use eframe::egui;
use app::EvidenceManagerApp;

fn main() -> Result<(), eframe::Error> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([1200.0, 800.0])
            .with_min_inner_size([800.0, 600.0]),
        ..Default::default()
    };

    eframe::run_native(
        "Evidence Manager",
        options,
        Box::new(|_cc| Ok(Box::new(EvidenceManagerApp::new()))),
    )
}
