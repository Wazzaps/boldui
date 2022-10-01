use boldui_protocol::{bincode, serde};
use byteorder::{WriteBytesExt, LE};
use std::io::Write;

pub(crate) trait SerdeSender {
    fn send<T: serde::Serialize>(&mut self, val: &T) -> Result<(), Box<dyn std::error::Error>>;
}

impl<W: Write> SerdeSender for W {
    fn send<T: serde::Serialize>(&mut self, val: &T) -> Result<(), Box<dyn std::error::Error>> {
        let msg = bincode::serialize(val)?;
        self.write_u32::<LE>(msg.len() as u32)?;
        self.write_all(&msg)?;
        self.flush()?;
        Ok(())
    }
}
