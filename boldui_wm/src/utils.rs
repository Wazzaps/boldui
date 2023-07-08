use boldui_protocol::{bincode, serde};
use std::pin::Pin;
use tokio::io::{AsyncWrite, AsyncWriteExt};

pub fn unwrap_or_str<'a>(s: &'a Option<String>, default: &'static str) -> &'a str {
    s.as_ref().map(|s| s.as_str()).unwrap_or(default)
}

#[async_trait::async_trait]
pub(crate) trait SerdeSender {
    async fn send<T: serde::Serialize>(&mut self, val: &T) -> anyhow::Result<()>;
}

#[async_trait::async_trait]
impl<W: AsyncWrite + Send + Unpin> SerdeSender for W {
    fn send<'a, 'b, 'c, T>(
        &'a mut self,
        val: &'b T,
    ) -> Pin<Box<dyn std::future::Future<Output = anyhow::Result<()>> + Send + 'c>>
    where
        T: 'c + serde::Serialize,
        'a: 'c,
        'b: 'c,
        Self: 'c,
    {
        let msg = bincode::serialize(val).unwrap(); // FIXME: unwrap
        Box::pin(async move {
            self.write_u32_le(msg.len() as u32).await?;
            self.write_all(&msg).await?;
            self.flush().await?;
            Ok(())
        })
    }
}
