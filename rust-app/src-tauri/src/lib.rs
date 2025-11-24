// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
mod api_client;
mod security;

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Serialize, Deserialize, Debug)]
struct DatabaseConfig {
    driver_type: String,
    config: HashMap<String, serde_json::Value>,
}

#[derive(Serialize, Deserialize, Debug)]
struct DatabaseResponse {
    success: bool,
    message: String,
    driver_type: Option<String>,
    tables: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug)]
struct SimpleResponse {
    success: bool,
    message: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct DatabaseStatus {
    connected: bool,
    driver_type: Option<String>,
    tables: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug)]
struct Driver {
    name: String,
    description: String,
    required_fields: Vec<String>,
    field_types: HashMap<String, String>,
}

#[tauri::command]
async fn send_query(question: String) -> Result<String, String> {
    // Validação de segurança
    if !security::validate_input(&question) {
        return Err("Entrada bloqueada por segurança!".to_string());
    }

    // Chama a API Python
    match api_client::send_query(&question).await {
        Ok(response) => {
            if response.success {
                let mut result_text = String::new();
                
                // Adiciona resposta da IA se houver
                if let Some(ai_response) = &response.ai_response {
                    if !ai_response.is_empty() {
                        result_text.push_str(&format!("🤖 IA: {}\n\n", ai_response));
                    }
                }
                
                // Adiciona SQL se houver
                if let Some(sql) = &response.sql {
                    if !sql.is_empty() {
                        result_text.push_str(&format!("📝 SQL: {}\n\n", sql));
                    }
                }
                
                // Adiciona resultado se houver
                if let Some(result_data) = &response.result {
                    result_text.push_str("📊 Resultado:\n");
                    if result_data.is_array() {
                        let results = result_data.as_array().unwrap();
                        if results.is_empty() {
                            result_text.push_str("Nenhum resultado encontrado.\n");
                        } else {
                            result_text.push_str(&format!("{} registros encontrados:\n", results.len()));
                            for (i, record) in results.iter().enumerate() {
                                if i < 5 { // Mostra apenas os primeiros 5 registros
                                    result_text.push_str(&format!("  {}: {}\n", i + 1, record));
                                }
                            }
                            if results.len() > 5 {
                                result_text.push_str(&format!("  ... e mais {} registros\n", results.len() - 5));
                            }
                        }
                    } else {
                        result_text.push_str(&format!("{}\n", result_data));
                    }
                }
                
                // Adiciona contagem de linhas se houver
                if let Some(row_count) = response.row_count {
                    result_text.push_str(&format!("\n📈 Total de registros: {}", row_count));
                }
                
                Ok(result_text)
            } else {
                let error_msg = response.error.unwrap_or("Erro desconhecido".to_string());
                Err(format!("❌ {}", error_msg))
            }
        }
        Err(err) => Err(format!("Erro ao comunicar com backend: {}", err))
    }
}

#[tauri::command]
async fn get_database_drivers() -> Result<HashMap<String, Driver>, String> {
    let client = reqwest::Client::new();
    
    match client.get("http://localhost:8000/drivers")
        .send()
        .await
    {
        Ok(response) => {
            match response.json::<HashMap<String, Driver>>().await {
                Ok(drivers) => Ok(drivers),
                Err(e) => Err(format!("Erro ao processar resposta: {}", e))
            }
        }
        Err(e) => Err(format!("Erro ao conectar com backend: {}", e))
    }
}

#[tauri::command]
async fn connect_database(driver_type: String, config: HashMap<String, serde_json::Value>) -> Result<DatabaseResponse, String> {
    let client = reqwest::Client::new();
    
    let payload = DatabaseConfig {
        driver_type,
        config,
    };
    
    match client.post("http://localhost:8000/database/connect")
        .json(&payload)
        .send()
        .await
    {
        Ok(response) => {
            println!("{:?}", response);
            let status = response.status();
            let text = response.text().await.unwrap_or("Erro ao ler resposta".to_string());
            println!("Status: {}, Resposta do servidor: {}", status, text);
            
            match serde_json::from_str::<DatabaseResponse>(&text) {
                Ok(result) => Ok(result),
                Err(e) => Err(format!("Erro ao processar JSON: {} - Resposta: {}", e, text))
            }
        }
        Err(e) => Err(format!("Erro ao conectar com backend: {}", e))
    }
}

#[tauri::command]
async fn disconnect_database() -> Result<SimpleResponse, String> {
    let client = reqwest::Client::new();
    
    match client.post("http://localhost:8000/database/disconnect")
        .send()
        .await
    {
        Ok(response) => {
            match response.json::<SimpleResponse>().await {
                Ok(result) => Ok(result),
                Err(e) => Err(format!("Erro ao processar resposta: {}", e))
            }
        }
        Err(e) => Err(format!("Erro ao conectar com backend: {}", e))
    }
}

#[tauri::command]
async fn get_database_status() -> Result<DatabaseStatus, String> {
    let client = reqwest::Client::new();
    
    match client.get("http://localhost:8000/database/status")
        .send()
        .await
    {
        Ok(response) => {
            match response.json::<DatabaseStatus>().await {
                Ok(status) => Ok(status),
                Err(e) => Err(format!("Erro ao processar resposta: {}", e))
            }
        }
        Err(e) => Err(format!("Erro ao conectar com backend: {}", e))
    }
}

#[tauri::command]
async fn create_sample_data() -> Result<SimpleResponse, String> {
    let client = reqwest::Client::new();
    
    match client.post("http://localhost:8000/database/sample-data")
        .send()
        .await
    {
        Ok(response) => {
            match response.json::<SimpleResponse>().await {
                Ok(result) => Ok(result),
                Err(e) => Err(format!("Erro ao processar resposta: {}", e))
            }
        }
        Err(e) => Err(format!("Erro ao conectar com backend: {}", e))
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            send_query, 
            get_database_drivers,
            connect_database,
            disconnect_database,
            get_database_status,
            create_sample_data
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
