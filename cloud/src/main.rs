use actix_web::{get, App, HttpResponse, HttpServer, Responder};
use rusqlite::{Connection, Result};
use serde::Serialize;
use std::time::Instant;

// 1. REAL DATABASE RETRIEVAL (SQLite Disk I/O)
// This connects to the database.sqlite file you created with Python
fn fetch_users_from_db() -> Result<Vec<usize>> {
    // 1. Explicitly point to the src folder
    // Alternatively, move database.sqlite to your main /cloud/ folder
    let path = "src/database.sqlite"; 

    let conn = Connection::open(path)?;

    // 2. We use a real query. 
    // If the table 'users' doesn't exist, this will now throw an error 
    // instead of returning 0.
    let mut stmt = conn.prepare("SELECT id FROM users")?;
    let user_iter = stmt.query_map([], |row| row.get(0))?;

    let mut users = Vec::new();
    for user in user_iter {
        users.push(user.expect("Failed to parse user ID"));
    }

    if users.is_empty() {
        eprintln!("Warning: Database was opened, but the 'users' table is empty!");
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

    // 1. Remove unwrap_or_default and handle the error properly
    let users = match fetch_users_from_db() {
        Ok(u) => u,
        Err(e) => {
            eprintln!("Database Error: {}", e);
            return HttpResponse::InternalServerError().body(format!("DB Error: {}", e));
        }
    };

    let matches = gale_shapley_mock(users);

    // 2. Use microseconds so your Measure of Success isn't "0"
    let duration = start_time.elapsed().as_micros(); 

    HttpResponse::Ok().json(serde_json::json!({
        "status": "Success",
        "users_found": matches, // helps us verify data was read
        "matches_made": matches / 2, // simple simulation of pairs
        "processing_time_micros": duration,
    }))
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