// Copyright (c) Facebook, Inc. and its affiliates
// SPDX-License-Identifier: MIT OR Apache-2.0

use crate::{
    indent::{IndentConfig, IndentedWriter},
    CodeGeneratorConfig,
};
use serde_reflection::{ContainerFormat, Format, Named, Registry, VariantFormat};
use std::{
    collections::BTreeMap,
    io::{Result, Write},
};

/// Main configuration object for code-generation in Python.
pub struct CodeGenerator<'a> {
    /// Language-independent configuration.
    config: &'a CodeGeneratorConfig,
}

/// Shared state for the code generation of a Python source file.
struct BtEmitter<'a, T> {
    /// Writer.
    out: IndentedWriter<T>,
    /// Generator.
    generator: &'a CodeGenerator<'a>,
    /// Current namespace (e.g. vec!["my_package", "my_module", "MyClass"])
    current_namespace: Vec<String>,
}

impl<'a> CodeGenerator<'a> {
    /// Create a Python code generator for the given config.
    pub fn new(config: &'a CodeGeneratorConfig) -> Self {
        if config.c_style_enums {
            panic!("Bt010 does not support generating c-style enums");
        }
        Self { config }
    }

    /// Write container definitions in Python.
    pub fn output(&self, out: &mut dyn Write, registry: &Registry) -> Result<()> {
        let current_namespace = self
            .config
            .module_name
            .split('.')
            .map(String::from)
            .collect();
        let mut emitter = BtEmitter {
            out: IndentedWriter::new(out, IndentConfig::Space(4)),
            generator: self,
            current_namespace,
        };
        emitter.output_preamble()?;
        for (name, format) in registry {
            emitter.output_struct_prototype(name, format)?;
        }
        for (name, format) in registry {
            emitter.output_container(name, format)?;
        }
        emitter.output_postamble()?;
        Ok(())
    }
}

impl<'a, T> BtEmitter<'a, T>
where
    T: Write,
{
    fn output_preamble(&mut self) -> Result<()> {
        writeln!(
            self.out,
            r#"
LittleEndian();

struct String {{
    uint64 len;
    char data[len];
}};

struct Bytes {{
    uint64 len;
    ubyte data[len];
}};
        "#
        )?;
        Ok(())
    }

    fn output_postamble(&mut self) -> Result<()> {
        writeln!(
            self.out,
            r#"
char magic[7];
if (Memcmp(magic, "BOLDUI\x01", sizeof("BOLDUI\x01")-1) == 0) {{
    A2RHelloResponse hello_res;
    A2RExtendedHelloResponse ext_hello_res;
    while (!FEof()) {{
        uint32 msg_len;
        A2RMessage msg;
    }}
}}
        "#
        )?;
        Ok(())
    }

    fn quote_type(&self, format: &Format) -> String {
        use Format::*;
        match format {
            TypeName(x) => {
                // eprintln!("quote_type: {}", x);
                // self.quote_qualified_name(x)
                x.into()
            }
            Unit => {
                panic!("Unit type not supported")
            }
            Bool => "bool".into(),
            I8 => "byte".into(),
            I16 => "int16".into(),
            I32 => "int32".into(),
            I64 => "int64".into(),
            I128 => "int128".into(),
            U8 => "ubyte".into(),
            U16 => "uint16".into(),
            U32 => "uint32".into(),
            U64 => "uint64".into(),
            U128 => "uint128".into(),
            F32 => "float".into(),
            F64 => "double".into(),
            Char => "char".into(),
            Str => "String".into(),
            Bytes => "Bytes".into(),

            Option(format) => {
                format!(
                    "struct {{ ubyte is_some; if (is_some) {{ {} item; }} }}",
                    self.quote_type(format)
                )
            }
            Seq(format) => format!(
                "struct {{ uint64 len; {} items[len] <optimize=false>; }}",
                self.quote_type(format)
            ),
            Map { key, value } => format!(
                "struct {{ uint64 len; struct {{ {} key; {} value; }} items[len] <optimize=false>; }}",
                self.quote_type(key),
                self.quote_type(value)
            ),
            Tuple(formats) => {
                if formats.is_empty() {
                    "struct {{}}".into()
                } else {
                    let fields = formats
                        .iter()
                        .enumerate()
                        .map(|(i, x)| format!("{} f{};", self.quote_type(x), i))
                        .collect::<Vec<_>>()
                        .join(" ");
                    format!("struct {{ {} }}", fields)
                    // format!("typing.Tuple[{}]", self.quote_types(formats))
                }
            }
            // FIXME
            TupleArray { content: _, size: _ } => {
                unimplemented!();
                // format!(
                //     "typing.Tuple[{}]",
                //     self.quote_types(&vec![content.as_ref().clone(); *size])
                // )
            }, // Sadly, there are no fixed-size arrays in python.

            Variable(_) => panic!("unexpected value"),
        }
    }

    fn output_comment(&mut self, name: &str) -> Result<()> {
        let mut path = self.current_namespace.clone();
        path.push(name.to_string());
        if let Some(doc) = self.generator.config.comments.get(&path) {
            let text = textwrap::indent(doc, "// ").replace("\n\n", "\n//\n");
            write!(self.out, "\n{}", text)?;
        }
        Ok(())
    }

    // fn output_custom_code(&mut self) -> Result<bool> {
    //     match self
    //         .generator
    //         .config
    //         .custom_code
    //         .get(&self.current_namespace)
    //     {
    //         Some(code) => {
    //             writeln!(self.out, "\n{}", code)?;
    //             Ok(true)
    //         }
    //         None => Ok(false),
    //     }
    // }

    fn output_fields(&mut self, fields: &[Named<Format>]) -> Result<()> {
        // if fields.is_empty() {
        //     writeln!(self.out, "pass")?;
        //     return Ok(());
        // }
        for field in fields {
            writeln!(
                self.out,
                "{} {};",
                self.quote_type(&field.value),
                field.name,
            )?;
        }
        Ok(())
    }

    fn output_variant(
        &mut self,
        _base: &str,
        name: &str,
        index: u32,
        variant: &VariantFormat,
    ) -> Result<()> {
        use VariantFormat::*;
        let fields = match variant {
            Unit => Vec::new(),
            NewType(format) => vec![Named {
                name: "value".to_string(),
                value: format.as_ref().clone(),
            }],
            Tuple(formats) => vec![Named {
                name: "value".to_string(),
                value: Format::Tuple(formats.clone()),
            }],
            Struct(fields) => fields.clone(),
            Variable(_) => panic!("incorrect value"),
        };

        self.output_comment(name)?;
        writeln!(self.out, "if (_tag == {}) {{", index)?;
        self.out.indent();
        self.output_fields(&fields)?;
        self.out.unindent();
        writeln!(self.out, "}}")?;
        writeln!(self.out)
    }

    fn output_enum_container(
        &mut self,
        name: &str,
        variants: &BTreeMap<u32, Named<VariantFormat>>,
    ) -> Result<()> {
        self.output_comment(name)?;
        writeln!(self.out, "\nenum <uint32> {}_TAGS {{", name)?;
        self.out.indent();
        for (index, variant) in variants {
            writeln!(self.out, "{}_{} = {},", name, &variant.name, index)?;
        }
        self.out.unindent();
        writeln!(self.out, "}};")?;

        writeln!(self.out, "\nstruct {} {{", name)?;
        self.out.indent();
        self.current_namespace.push(name.to_string());
        writeln!(self.out, "enum {}_TAGS _tag;\n", name)?;
        for (index, variant) in variants {
            self.output_variant(name, &variant.name, *index, &variant.value)?;
        }
        self.out.unindent();

        self.current_namespace.pop();
        writeln!(self.out, "}};")?;

        Ok(())
    }

    fn output_struct_prototype(&mut self, name: &str, format: &ContainerFormat) -> Result<()> {
        use ContainerFormat::*;
        if let UnitStruct = format {
            // Don't generate UnitStructs, they will only cause confusion
            return Ok(());
        };

        writeln!(self.out, "struct {};", name)?;
        writeln!(self.out)
    }

    fn output_container(&mut self, name: &str, format: &ContainerFormat) -> Result<()> {
        use ContainerFormat::*;
        let fields = match format {
            UnitStruct => {
                // Don't generate UnitStructs, they will only cause confusion
                return Ok(());
            }
            NewTypeStruct(format) => vec![Named {
                name: "value".to_string(),
                value: format.as_ref().clone(),
            }],
            TupleStruct(formats) => {
                eprintln!("Making TupleStruct: {}: {:?}", name, formats);
                vec![Named {
                    name: "value".to_string(),
                    value: Format::Tuple(formats.clone()),
                }]
            }
            Struct(fields) => fields.clone(),
            Enum(variants) => {
                // Enum case.
                self.output_enum_container(name, variants)?;
                return Ok(());
            }
        };
        // Struct case.
        self.output_comment(name)?;
        writeln!(self.out, "\nstruct {} {{", name)?;
        self.out.indent();
        self.current_namespace.push(name.to_string());
        self.output_fields(&fields)?;
        // for encoding in &self.generator.config.encodings {
        //     self.output_serialize_method_for_encoding(name, *encoding)?;
        //     self.output_deserialize_method_for_encoding(name, *encoding)?;
        // }
        // self.output_custom_code()?;
        self.current_namespace.pop();
        self.out.unindent();
        writeln!(self.out, "}};")?;
        writeln!(self.out)
    }
}

// /// Installer for generated source files in Python.
// pub struct Installer {
//     install_dir: PathBuf,
// }
//
// impl Installer {
//     pub fn new(install_dir: PathBuf) -> Self {
//         Installer { install_dir }
//     }
//
//     fn create_module_init_file(&self, name: &str) -> Result<std::fs::File> {
//         let dir_path = self.install_dir.join(name);
//         std::fs::create_dir_all(&dir_path)?;
//         std::fs::File::create(dir_path.join("__init__.py"))
//     }
// }
//
// impl crate::SourceInstaller for Installer {
//     type Error = Box<dyn std::error::Error>;
//
//     fn install_module(
//         &self,
//         config: &crate::CodeGeneratorConfig,
//         registry: &Registry,
//     ) -> std::result::Result<(), Self::Error> {
//         let mut file = self.create_module_init_file(&config.module_name)?;
//         let generator =
//             CodeGenerator::new(config).with_serde_package_name(self.serde_package_name.clone());
//         generator.output(&mut file, registry)?;
//         Ok(())
//     }
//
//     fn install_serde_runtime(&self) -> std::result::Result<(), Self::Error> {
//         let mut file = self.create_module_init_file("serde_types")?;
//         write!(
//             file,
//             "{}",
//             self.fix_serde_package(include_str!("../runtime/python/serde_types/__init__.py"))
//         )?;
//         let mut file = self.create_module_init_file("serde_binary")?;
//         write!(
//             file,
//             "{}",
//             self.fix_serde_package(include_str!("../runtime/python/serde_binary/__init__.py"))
//         )?;
//         Ok(())
//     }
//
//     fn install_bincode_runtime(&self) -> std::result::Result<(), Self::Error> {
//         let mut file = self.create_module_init_file("bincode")?;
//         write!(
//             file,
//             "{}",
//             self.fix_serde_package(include_str!("../runtime/python/bincode/__init__.py"))
//         )?;
//         Ok(())
//     }
//
//     fn install_bcs_runtime(&self) -> std::result::Result<(), Self::Error> {
//         let mut file = self.create_module_init_file("bcs")?;
//         write!(
//             file,
//             "{}",
//             self.fix_serde_package(include_str!("../runtime/python/bcs/__init__.py"))
//         )?;
//         Ok(())
//     }
// }
