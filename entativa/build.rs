fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .build_client(true)
        .build_server(false)
        .compile(
            &[
                "../piercer-auth-ui/proto/auth.proto",
                "../piercer-auth-ui/proto/shared.proto",
                "proto/entativa.proto",
            ],
            &["../piercer-auth-ui/proto", "proto"],
        )?;
    Ok(())
}
