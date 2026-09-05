// envcheck — compares .env against .env.example and reports any keys
// present in the example (i.e. expected) but missing from the real .env.
// Run before starting the app or deploying:
//
//   cargo run --release -- .

use std::collections::HashSet;
use std::env;
use std::fs;
use std::process::exit;

fn parse_keys(path: &str) -> HashSet<String> {
    let mut keys = HashSet::new();
    if let Ok(contents) = fs::read_to_string(path) {
        for line in contents.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            if let Some((key, _)) = line.split_once('=') {
                keys.insert(key.trim().to_string());
            }
        }
    }
    keys
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let dir = if args.len() > 1 { &args[1] } else { "." };

    let example_keys = parse_keys(&format!("{}/.env.example", dir));
    let actual_keys = parse_keys(&format!("{}/.env", dir));

    if example_keys.is_empty() {
        eprintln!("No .env.example found (or it's empty) in {}", dir);
        exit(2);
    }

    let mut missing: Vec<&String> = example_keys.difference(&actual_keys).collect();
    missing.sort();

    if missing.is_empty() {
        println!(
            "OK: all {} expected env var(s) are present in .env",
            example_keys.len()
        );
        return;
    }

    println!("Missing {} env var(s) from .env:", missing.len());
    for key in &missing {
        println!("  - {}", key);
    }
    exit(1);
}
