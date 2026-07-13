use std::path::PathBuf;

fn validate_folder_path(path: &str) -> Result<PathBuf, String> {
    let canonical = std::fs::canonicalize(path).map_err(|e| e.to_string())?;
    if !canonical.is_dir() {
        return Err(format!("Not a directory: {}", canonical.display()));
    }
    Ok(canonical)
}

#[tauri::command]
async fn open_folder(path: String) -> Result<(), String> {
    let path = validate_folder_path(&path)?;
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("explorer")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::validate_folder_path;
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn unique_test_path(name: &str) -> std::path::PathBuf {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("clock should be after unix epoch")
            .as_nanos();
        std::env::temp_dir().join(format!("polyanalyzer-{name}-{nonce}"))
    }

    #[test]
    fn accepts_existing_directories() {
        let path = unique_test_path("directory");
        fs::create_dir(&path).expect("test directory should be created");

        let validated = validate_folder_path(path.to_str().expect("utf-8 path"));

        assert_eq!(
            validated.expect("directory should be accepted"),
            fs::canonicalize(&path).expect("test directory should canonicalize"),
        );
        fs::remove_dir(path).expect("test directory should be removed");
    }

    #[test]
    fn rejects_files_and_missing_paths() {
        let file = unique_test_path("file");
        fs::write(&file, b"data").expect("test file should be created");
        let missing = unique_test_path("missing");

        assert!(validate_folder_path(file.to_str().expect("utf-8 path")).is_err());
        assert!(validate_folder_path(missing.to_str().expect("utf-8 path")).is_err());
        fs::remove_file(file).expect("test file should be removed");
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![open_folder])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
