pub fn validate_input(input: &str) -> bool {
    let blacklist = ["DROP", "DELETE", "INSERT", "UPDATE"];
    !blacklist.iter().any(|&word| input.to_lowercase().contains(&word.to_lowercase()))
}