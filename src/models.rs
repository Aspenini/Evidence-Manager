use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Person {
    pub id: Uuid,
    pub name: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub notes: String,
    pub tags: Vec<String>,
    pub information: Vec<PersonInfo>,
    #[serde(default)] // Backward compatibility
    pub quotes: Vec<Quote>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PersonInfo {
    pub id: Uuid,
    pub info_type: String,
    pub value: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Quote {
    pub id: Uuid,
    pub person_id: Uuid,
    pub quote: String,
    pub date: String,
    pub time: Option<String>,
    pub place: Option<String>,
    pub created_at: DateTime<Utc>,
}

impl Person {
    pub fn new(name: String) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4(),
            name,
            created_at: now,
            updated_at: now,
            notes: String::new(),
            tags: Vec::new(),
            information: Vec::new(),
            quotes: Vec::new(),
        }
    }

    pub fn update_timestamp(&mut self) {
        self.updated_at = Utc::now();
    }

    pub fn folder_name(&self) -> String {
        self.name.replace(' ', "_")
    }

    pub fn add_information(&mut self, info_type: String, value: String) {
        let info = PersonInfo {
            id: Uuid::new_v4(),
            info_type,
            value,
            created_at: Utc::now(),
        };
        self.information.push(info);
        self.update_timestamp();
    }

    pub fn remove_information(&mut self, info_id: Uuid) {
        self.information.retain(|info| info.id != info_id);
        self.update_timestamp();
    }

    pub fn add_quote(&mut self, quote: String, date: String, time: Option<String>, place: Option<String>) {
        let new_quote = Quote {
            id: Uuid::new_v4(),
            person_id: self.id,
            quote,
            date,
            time,
            place,
            created_at: Utc::now(),
        };
        self.quotes.push(new_quote);
        self.update_timestamp();
    }

    pub fn remove_quote(&mut self, quote_id: Uuid) {
        self.quotes.retain(|quote| quote.id != quote_id);
        self.update_timestamp();
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceFile {
    pub id: Uuid,
    pub person_id: Uuid,
    pub file_path: PathBuf,
    pub file_type: EvidenceType,
    pub original_name: String,
    pub size: u64,
    pub created_at: DateTime<Utc>,
    pub notes: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum EvidenceType {
    Image,
    Audio,
    Video,
    Document,
    Quote,
}

impl EvidenceType {
    pub fn from_extension(ext: &str) -> Option<Self> {
        let ext = ext.to_lowercase();
        match ext.as_str() {
            "jpg" | "jpeg" | "png" | "gif" | "bmp" | "tiff" | "webp" => Some(EvidenceType::Image),
            "mp3" | "wav" | "flac" | "aac" | "ogg" | "m4a" => Some(EvidenceType::Audio),
            "mp4" | "avi" | "mov" | "wmv" | "flv" | "webm" | "mkv" => Some(EvidenceType::Video),
            "pdf" | "doc" | "docx" | "txt" | "rtf" => Some(EvidenceType::Document),
            _ => None,
        }
    }

    pub fn folder_name(&self) -> &'static str {
        match self {
            EvidenceType::Image => "images",
            EvidenceType::Audio => "audio",
            EvidenceType::Video => "videos",
            EvidenceType::Document => "documents",
            EvidenceType::Quote => "quotes",
        }
    }
}

