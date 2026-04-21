//! Entativa client configuration.

#[derive(Debug, Clone)]
pub struct Config {
    pub auth_url:      String,
    pub entativa_url:  String,
}

impl Config {
    pub fn from_env() -> anyhow::Result<Self> {
        Ok(Self {
            auth_url:     std::env::var("AUTH_URL")
                              .unwrap_or_else(|_| "http://localhost:50050".into()),
            entativa_url: std::env::var("ENTATIVA_URL")
                              .unwrap_or_else(|_| "http://localhost:50051".into()),
        })
    }
}
