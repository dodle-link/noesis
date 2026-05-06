//! Tests for nos-specific configuration directories.

use fish::env::{environment::Environment, EnvStack};
use fish::parser::Parser;
use fish::wchar::{wstr, WString, L};
use std::env;
use std::fs::{self, File};
use std::io::Write;
use std::path::Path;
use tempfile::TempDir;

// Helper to run a fish code snippet and return the output
fn run_command(parser: &Parser, cmd: &str) -> WString {
    use fish::common::str2wcstring;
    use fish::io::{IoChain, IoStreams};
    use fish::io::OutputStream::String as StringOutput;
    use std::cell::RefCell;

    let mut output = StringOutput(Default::default());
    let io_chain = IoChain::new();
    let mut streams = IoStreams::new(&mut output, &mut output, &io_chain);

    let cmd_wstr = str2wcstring(cmd.as_bytes());
    let _ = parser.eval(&cmd_wstr, streams.io_chain());
    
    output.0.borrow().clone()
}

#[test]
fn test_nos_environment_variables() {
    let env = EnvStack::new();
    let parser = Parser::new(&env, fish::parser::CancelBehavior::Jump);
    
    // First source our standard config that sets up basic nos variables
    run_command(&parser, "source /Users/plugio/Documents/GitHub/nos/share/nos_config.nos");
    
    // Check that the nos-specific environment variables are set
    assert!(parser.vars().get(L!("NOS_EXTENSIONS_ENABLED")).is_some(), 
            "NOS_EXTENSIONS_ENABLED variable not set");
    
    assert!(parser.vars().get(L!("NOS_FISH_COMPATIBILITY")).is_some(),
            "NOS_FISH_COMPATIBILITY variable not set");
}

#[test]
fn test_nos_function_execution() {
    let env = EnvStack::new();
    let parser = Parser::new(&env, fish::parser::CancelBehavior::Jump);
    
    // Set function path to our share/functions directory
    run_command(&parser, "set fish_function_path /Users/plugio/Documents/GitHub/nos/share/functions");
    
    // Source both function versions
    run_command(&parser, "source /Users/plugio/Documents/GitHub/nos/share/functions/test_extension.fish");
    run_command(&parser, "source /Users/plugio/Documents/GitHub/nos/share/functions/test_extension.nos");
    
    // Run the function and verify we get the nos version
    let output = run_command(&parser, "test_extension");
    assert!(output.contains(L!("This is the NOS version")), 
            "Function did not use the .nos version");
    
    // Check the global variable that indicates which version ran
    let source = run_command(&parser, "echo $test_extension_source");
    assert!(source.contains(L!("nos")), 
            "Function did not set the variable indicating nos source");
}
