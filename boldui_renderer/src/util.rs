use boldui_protocol::{bincode, serde};
use byteorder::{WriteBytesExt, LE};
use nix::libc::{EAGAIN, EWOULDBLOCK};
use std::io::{Read, Write};

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

pub(crate) trait ReadExt {
    fn discard_until_eof(&mut self) -> std::io::Result<usize>;
}

impl ReadExt for std::fs::File {
    fn discard_until_eof(&mut self) -> std::io::Result<usize> {
        let mut counter = 0;
        let mut tmp_buf = [0; 32];
        loop {
            match self.read(&mut tmp_buf) {
                // Got all bytes, we're done
                Ok(0) => break,
                // Probably more bytes to come
                Ok(i) => {
                    counter += i;
                }
                // No more bytes, we're done
                Err(e)
                    if e.raw_os_error()
                        .map(|code| code == EAGAIN || code == EWOULDBLOCK)
                        .unwrap_or(false) =>
                {
                    break
                }
                // Something else
                Err(e) => return Err(e),
            }
        }
        Ok(counter)
    }
}
