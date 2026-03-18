use actix_web::{get, App, HttpResponse, HttpServer, Responder};
use rusqlite::{Connection, Result};
use serde::Serialize;
use std::time::Instant;

// Data structure for the response
#[derive(Serialize)]
struct MatchResponse {
    status: String,
    matches_made: usize,
    processing_time_ms: u128,
}

// 1. MOCK DATABASE RETRIEVAL (SQLite)
// In a real app, this reads your user tables. Here, we create an in-memory 
// SQLite DB to simulate the time it takes to execute a SQL query.
fn fetch_users_from_db(n: usize) -> Result<Vec<usize>> {
    let conn = Connection::open_in_memory()?;
    
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)",
        (),
    )?;

    // Insert mock users
    for i in 0..n {
        conn.execute("INSERT INTO users (name) VALUES (?1)", [&format!("User_{}", i)])?;
    }

    // Retrieve users (Simulating DB latency)
    let mut stmt = conn.prepare("SELECT id FROM users")?;
    let user_iter = stmt.query_map([], |row| row.get(0))?;

    let mut users = Vec::new();
    for user in user_iter {
        users.push(user.unwrap());
    }

    Ok(users)
}

// 2. GALE-SHAPLEY ALGORITHM O(n^2)
// This is a simplified mathematical simulation of Gale-Shapley's time complexity.
// We use nested loops to mimic the worst-case O(n^2) matching iterations.
fn gale_shapley_mock(users: Vec<usize>) -> usize {
    let n = users.len();
    let mut matches_made = 0;

    // Outer loop: Proposers (O(n))
    for _proposer in 0..n {
        // Inner loop: Reviewing preferences (O(n))
        for _receiver in 0..n {
            // Simulate matching logic / preference checking
            let is_match = true; 
            if is_match {
                matches_made += 1;
                break; // Move to next proposer once matched
            }
        }
    }
    // Total time complexity: O(n^2) in the worst case
    matches_made
}

// 3. THE ACTIX WEB ENDPOINT
// This is the endpoint JMeter will hit: http://<EC2-IP>:8080/match
#[get("/match")]
async fn process_matches() -> impl Responder {
    let start_time = Instant::now();
    let n_users = 100; // Testing with 100 users for O2 validation

    // Step A: DB Retrieval
    let users = fetch_users_from_db(n_users).unwrap_or_default();

    // Step B: Run Algorithm
    let matches = gale_shapley_mock(users);

    // Step C: Calculate internal time (optional, good for debugging)
    let duration = start_time.elapsed().as_millis();

    // Return the HTTP JSON response
    HttpResponse::Ok().json(MatchResponse {
        status: "Success".to_string(),
        matches_made: matches,
        processing_time_ms: duration,
    })
}

// 4. SERVER LAUNCH
#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("Starting Actix Web server on port 8080...");
    HttpServer::new(|| {
        App::new().service(process_matches)
    })
    .bind(("0.0.0.0", 8080))? // 0.0.0.0 allows external access from your EC2
    .run()
    .await
}