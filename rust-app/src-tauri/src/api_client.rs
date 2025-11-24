use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Serialize)]
pub struct QueryRequest {
    pub question: String,
}

#[derive(Deserialize)]
pub struct QueryResponse {
    pub success: bool,
    pub sql: Option<String>,
    pub result: Option<Value>,
    pub ai_response: Option<String>,
    pub error: Option<String>,
    pub tables_available: Option<Vec<String>>,
    pub row_count: Option<usize>,
}

pub async fn send_query(question: &str) -> Result<QueryResponse, reqwest::Error> {
    let client = reqwest::Client::new();
    let payload = QueryRequest {
        question: question.to_string(),
    };

    let res = client.post("http://localhost:8000/ai/process")
        .json(&payload)
        .send()
        .await?
        .json::<QueryResponse>()
        .await?;

    Ok(res)
}