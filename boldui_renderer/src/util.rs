use boldui_protocol::{bincode, serde};
use byteorder::{WriteBytesExt, LE};
use nix::libc::{EAGAIN, EWOULDBLOCK};
use num_traits::Float;
use std::io::{Read, Write};
use std::mem::size_of;
use tracing::debug;

pub(crate) trait SerdeSender {
    fn send<T: serde::Serialize>(&mut self, val: &T) -> Result<(), Box<dyn std::error::Error>>;
    fn send_with_u32<T: serde::Serialize>(
        &mut self,
        val: &T,
        extra: u32,
    ) -> Result<(), Box<dyn std::error::Error>>;
}

impl<W: Write> SerdeSender for W {
    fn send<T: serde::Serialize>(&mut self, val: &T) -> Result<(), Box<dyn std::error::Error>> {
        let msg = bincode::serialize(val)?;
        self.write_u32::<LE>(msg.len() as u32)?;
        self.write_all(&msg)?;
        self.flush()?;
        Ok(())
    }
    fn send_with_u32<T: serde::Serialize>(
        &mut self,
        val: &T,
        extra: u32,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let msg = bincode::serialize(val)?;
        debug!("Sending: {:?}", &msg);
        self.write_u32::<LE>(msg.len() as u32)?;
        self.write_u32::<LE>(extra)?;
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

pub(crate) trait FloatExt: Float {
    fn map_non_nan<F: Fn(Self) -> Self>(self, f: F) -> Self {
        if self.is_nan() {
            self
        } else {
            f(self)
        }
    }
}

impl FloatExt for f32 {}
impl FloatExt for f64 {}

pub unsafe fn any_as_u8_slice_mut<T: Sized>(p: &mut T) -> &mut [u8] {
    core::slice::from_raw_parts_mut((p as *mut T) as *mut u8, core::mem::size_of::<T>())
}

pub unsafe fn u8_slice_as_any<T: Sized>(p: &[u8]) -> &T {
    assert_eq!(p.len(), size_of::<T>(), "Wrong size");
    let ptr = p.as_ptr();
    assert_eq!(
        ptr as usize % std::mem::align_of::<T>(),
        0,
        "Wrong alignment"
    );
    (ptr as *const T).as_ref().unwrap_unchecked()
}
