//! Application-level state containers.

use crate::proto::entativa::VideoPayload;

/// Feed state — holds the current video list and cursor for pagination.
#[derive(Debug, Default)]
pub struct FeedState {
    pub videos:      Vec<VideoPayload>,
    pub next_cursor: Option<String>,
    pub loading:     bool,
    pub error:       Option<String>,
}

impl FeedState {
    pub fn set_loading(&mut self, v: bool) { self.loading = v; }

    pub fn append_page(&mut self, videos: Vec<VideoPayload>, next_cursor: String) {
        self.videos.extend(videos);
        self.next_cursor = if next_cursor.is_empty() { None } else { Some(next_cursor) };
        self.loading = false;
    }

    pub fn has_more(&self) -> bool { self.next_cursor.is_some() }
}
