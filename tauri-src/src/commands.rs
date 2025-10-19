use crate::app_state::AppState;
use crate::models::{EvidenceFile, EvidenceType, Person};
use anyhow::Result;
use serde::Deserialize;
use std::path::PathBuf;
use tauri::State;
use uuid::Uuid;

fn parse_uuid(id: &str) -> Result<Uuid> {
    Ok(Uuid::parse_str(id)?)
}

#[tauri::command]
pub fn list_persons(state: State<AppState>) -> Result<Vec<Person>, String> {
    let state = state.lock().map_err(|e| e.to_string())?;
    Ok(state.list_persons())
}

#[tauri::command]
pub fn add_person(state: State<AppState>, name: String) -> Result<Person, String> {
    let mut state = state.lock().map_err(|e| e.to_string())?;
    state.add_person(name).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn delete_person(state: State<AppState>, person_id: String) -> Result<(), String> {
    let id = parse_uuid(&person_id).map_err(|e| e.to_string())?;
    let mut state = state.lock().map_err(|e| e.to_string())?;
    state.delete_person(id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn add_information(
    state: State<AppState>,
    person_id: String,
    info_type: String,
    value: String,
) -> Result<Person, String> {
    let id = parse_uuid(&person_id).map_err(|e| e.to_string())?;
    let mut state = state.lock().map_err(|e| e.to_string())?;
    let person = state.get_person_mut(id).map_err(|e| e.to_string())?;
    person.add_information(info_type, value);
    state.save_person(person).map_err(|e| e.to_string())?;
    Ok(person.clone())
}

#[tauri::command]
pub fn remove_information(
    state: State<AppState>,
    person_id: String,
    info_id: String,
) -> Result<Person, String> {
    let person_id = parse_uuid(&person_id).map_err(|e| e.to_string())?;
    let info_id = parse_uuid(&info_id).map_err(|e| e.to_string())?;
    let mut state = state.lock().map_err(|e| e.to_string())?;
    let person = state.get_person_mut(person_id).map_err(|e| e.to_string())?;
    person.remove_information(info_id);
    state.save_person(person).map_err(|e| e.to_string())?;
    Ok(person.clone())
}

#[tauri::command]
pub fn add_quote(
    state: State<AppState>,
    person_id: String,
    quote: String,
    date: String,
    time: Option<String>,
    place: Option<String>,
) -> Result<Person, String> {
    let person_id = parse_uuid(&person_id).map_err(|e| e.to_string())?;
    let mut state = state.lock().map_err(|e| e.to_string())?;
    let person = state.get_person_mut(person_id).map_err(|e| e.to_string())?;
    person.add_quote(quote, date, time, place);
    state.save_person(person).map_err(|e| e.to_string())?;
    Ok(person.clone())
}

#[tauri::command]
pub fn remove_quote(
    state: State<AppState>,
    person_id: String,
    quote_id: String,
) -> Result<Person, String> {
    let person_id = parse_uuid(&person_id).map_err(|e| e.to_string())?;
    let quote_id = parse_uuid(&quote_id).map_err(|e| e.to_string())?;
    let mut state = state.lock().map_err(|e| e.to_string())?;
    let person = state.get_person_mut(person_id).map_err(|e| e.to_string())?;
    person.remove_quote(quote_id);
    state.save_person(person).map_err(|e| e.to_string())?;
    Ok(person.clone())
}

#[derive(Deserialize)]
pub struct ExportRequest {
    pub destination: String,
    pub person_ids: Option<Vec<String>>,
}

#[tauri::command]
pub fn export_archive(state: State<AppState>, request: ExportRequest) -> Result<(), String> {
    let mut state = state.lock().map_err(|e| e.to_string())?;

    let persons_to_export = if let Some(ids) = request.person_ids {
        ids.into_iter()
            .map(|id| parse_uuid(&id).map_err(|e| e.to_string()))
            .collect::<Result<Vec<_>, _>>()?
    } else {
        state.persons.iter().map(|p| p.id).collect()
    };

    let selected_persons = persons_to_export
        .into_iter()
        .map(|id| {
            state
                .get_person(id)
                .map(|p| p.clone())
                .map_err(|e| e.to_string())
        })
        .collect::<Result<Vec<_>, _>>()?;

    let path = PathBuf::from(request.destination);
    state
        .export_import_manager
        .export_to_ema(&path, &selected_persons, None)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn import_archive(state: State<AppState>, path: String) -> Result<Vec<Person>, String> {
    let mut state = state.lock().map_err(|e| e.to_string())?;
    let path = PathBuf::from(path);
    let persons = state
        .export_import_manager
        .import_from_ema(&path, None)
        .map_err(|e| e.to_string())?;

    state.persons = persons.clone();
    Ok(persons)
}

#[tauri::command]
pub fn scan_evidence(
    state: State<AppState>,
    person_id: String,
) -> Result<Vec<EvidenceFile>, String> {
    let id = parse_uuid(&person_id).map_err(|e| e.to_string())?;
    let state = state.lock().map_err(|e| e.to_string())?;
    state.scan_evidence(id).map_err(|e| e.to_string())
}

#[derive(Deserialize)]
pub struct AddEvidenceRequest {
    pub person_id: String,
    pub source_path: String,
    pub evidence_type: String,
}

#[tauri::command]
pub fn add_evidence(
    state: State<AppState>,
    request: AddEvidenceRequest,
) -> Result<EvidenceFile, String> {
    let person_id = parse_uuid(&request.person_id).map_err(|e| e.to_string())?;
    let evidence_type = EvidenceType::from_str(&request.evidence_type)
        .ok_or_else(|| format!("Unsupported evidence type: {}", request.evidence_type))?;
    let mut state = state.lock().map_err(|e| e.to_string())?;
    let source_path = PathBuf::from(request.source_path);
    state
        .copy_evidence(person_id, &source_path, evidence_type)
        .map_err(|e| e.to_string())
}
