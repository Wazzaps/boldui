pub fn unwrap_or_str<'a>(s: &'a Option<String>, default: &'static str) -> &'a str {
    s.as_ref().map(|s| s.as_str()).unwrap_or(default)
}
