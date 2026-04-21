//! Upload screen — video upload flow.
//!
//! Flow:
//!   1. User picks video from device gallery or camera
//!   2. Client-side transcode to H.265/HEVC (GPU via Blinc render pipeline)
//!   3. InitUpload RPC → get presigned S3 URL
//!   4. Upload directly to S3 (chunked, resumable)
//!   5. FinalizeUpload RPC → server processes, generates thumbnail, queues transcode fallback
//!   6. Navigate back to feed
//!
//! The transcode happens on-device before upload.
//! This keeps upload sizes small and ensures consistent codec across all videos.

use crate::client::EntativaClient;

pub struct UploadScreenState {
    pub video_path:    Option<std::path::PathBuf>,
    pub caption:       String,
    pub tags:          Vec<String>,
    pub progress:      f32,   // 0.0–1.0
    pub stage:         UploadStage,
    pub error:         Option<String>,
}

#[derive(Debug, Clone, PartialEq)]
pub enum UploadStage {
    Idle,
    Transcoding,
    Uploading,
    Finalizing,
    Done,
}

impl Default for UploadScreenState {
    fn default() -> Self {
        Self {
            video_path: None,
            caption:    String::new(),
            tags:       Vec::new(),
            progress:   0.0,
            stage:      UploadStage::Idle,
            error:      None,
        }
    }
}

impl UploadScreenState {
    pub fn can_upload(&self) -> bool {
        self.video_path.is_some() && self.stage == UploadStage::Idle
    }

    pub async fn start_upload(
        &mut self,
        _client:  &mut EntativaClient,
        _user_id: &str,
    ) -> anyhow::Result<()> {
        // TODO:
        // 1. self.stage = UploadStage::Transcoding
        //    transcode_to_h265(&self.video_path.unwrap())
        // 2. self.stage = UploadStage::Uploading
        //    client.init_upload(...) → presigned_url
        //    upload_to_s3(presigned_url, transcoded_file, |progress| self.progress = progress)
        // 3. self.stage = UploadStage::Finalizing
        //    client.finalize_upload(upload_id, caption, tags)
        // 4. self.stage = UploadStage::Done
        Ok(())
    }
}
