use boldui_protocol::*;
use serde_reflection::{Tracer, TracerConfig};
use std::mem::size_of;
use std::path::PathBuf;

pub fn main() {
    let mut tracer = Tracer::new(TracerConfig::default());
    // let mut samples = Samples::new();
    tracer
        .trace_simple_type::<A2RExtendedHelloResponse>()
        .unwrap();
    tracer.trace_simple_type::<A2RHelloResponse>().unwrap();
    tracer.trace_simple_type::<A2RMessage>().unwrap();
    tracer.trace_simple_type::<A2RReparentScene>().unwrap();
    tracer.trace_simple_type::<A2RUpdate>().unwrap();
    tracer.trace_simple_type::<A2RUpdateScene>().unwrap();
    tracer.trace_simple_type::<CmdsCommand>().unwrap();
    tracer.trace_simple_type::<Error>().unwrap();
    tracer.trace_simple_type::<HandlerBlock>().unwrap();
    tracer.trace_simple_type::<HandlerCmd>().unwrap();
    tracer.trace_simple_type::<OpsOperation>().unwrap();
    tracer.trace_simple_type::<R2AExtendedHello>().unwrap();
    tracer.trace_simple_type::<R2AHello>().unwrap();
    tracer.trace_simple_type::<R2AMessage>().unwrap();
    tracer.trace_simple_type::<R2AOpen>().unwrap();
    tracer.trace_simple_type::<R2AUpdate>().unwrap();
    tracer.trace_simple_type::<Value>().unwrap();
    tracer.trace_simple_type::<R2EAHello>().unwrap();
    tracer.trace_simple_type::<R2EAExtendedHello>().unwrap();
    tracer.trace_simple_type::<R2EAMessage>().unwrap();
    tracer.trace_simple_type::<R2EAOpen>().unwrap();
    tracer.trace_simple_type::<R2EAUpdate>().unwrap();
    tracer.trace_simple_type::<EA2RHelloResponse>().unwrap();
    tracer
        .trace_simple_type::<EA2RExtendedHelloResponse>()
        .unwrap();
    tracer.trace_simple_type::<EA2RMessage>().unwrap();
    tracer.trace_simple_type::<EventType>().unwrap();
    let registry = tracer.registry().unwrap();

    // Make sure type sizes are in check (do not depend on this, this is for internal use (prevent memory balooning))
    let value_size = size_of::<Value>();
    let value_max_size = 64;
    assert!(
        value_size <= value_max_size,
        "Value ({value_size}) is bigger than {value_max_size}"
    );
    let ops_operation_size = size_of::<OpsOperation>();
    let ops_operation_max_size = 64;
    assert!(
        ops_operation_size <= ops_operation_max_size,
        "Value ({ops_operation_size}) is bigger than {ops_operation_max_size}"
    );

    // // Write yaml representation
    // // (Broken: "serializing nested enums in YAML is not supported yet")
    // println!("Writing yaml representation...");
    // let yaml_registry = serde_yaml::to_string(&registry).unwrap();
    // std::fs::write("./protocol_bindings/protocol.yaml", &yaml_registry).unwrap();

    // Write python bindings
    let config = serde_generate::CodeGeneratorConfig::new("_boldui_protocol".to_string())
        .with_encodings(vec![serde_generate::Encoding::Bincode]);
    println!("Writing python bindings...");
    let mut py_source = Vec::new();
    let generator = serde_generate::python3::CodeGenerator::new(&config);
    generator.output(&mut py_source, &registry).unwrap();
    std::fs::write(
        "./boldui_protocol_bindings/python/boldui_protocol/_boldui_protocol.py",
        &py_source,
    )
    .unwrap();
    std::process::Command::new("black")
        .arg("--quiet")
        .arg("./boldui_protocol_bindings/python/boldui_protocol/_boldui_protocol.py")
        .spawn()
        .unwrap()
        .wait()
        .unwrap();

    // Write 010 Binary Template
    println!("Writing 010 binary template...");
    let mut bt010_source = Vec::new();
    let generator = serde_generate::bt010::CodeGenerator::new(&config);
    generator.output(&mut bt010_source, &registry).unwrap();
    std::fs::write("./boldui_protocol_bindings/template.bt", &bt010_source).unwrap();

    // Write C# bindings
    println!("Writing C# bindings...");
    let generator = serde_generate::csharp::CodeGenerator::new(&config);
    generator
        .write_source_files(
            PathBuf::from("./boldui_protocol_bindings/csharp"),
            &registry,
        )
        .unwrap();

    // Write Typescript bindings
    println!("Writing Typescript bindings...");
    let generator = serde_generate::typescript::CodeGenerator::new(&config);
    let mut ts_source = Vec::new();
    generator.output(&mut ts_source, &registry).unwrap();
    std::fs::write(
        "./boldui_protocol_bindings/typescript/_boldui_protocol/_boldui_protocol.ts",
        &ts_source,
    )
    .unwrap();

    println!("Done!");
}
