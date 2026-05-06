//! Tests for the dual file extension system.
//! Tests both .fish and .nos file recognition with proper precedence.

use fish::autoload::{has_asset, Autoload, AutoloadFile, AutoloadFileCache, AutoloadPath, AutoloadResult};
use fish::common::{str2wcstring, wcs2string};
use fish::env::{environment::Environment, EnvStack};
use fish::file_extension_handler::{
    find_file_with_any_extension, get_shell_extension, has_shell_extension, ShellExtension,
    strip_shell_extension,
};
use fish::parser::Parser;
use fish::wchar::{wstr, WString, L};
use fish::wutil::{file_id_for_path, wstat, INVALID_FILE_ID};
use std::fs::File;
use std::io::Write;
use std::path::Path;
use tempfile::tempdir;

#[test]
fn test_extension_recognition() {
    let fish_path = L!("/path/to/script.fish");
    let nos_path = L!("/path/to/script.nos");
    let other_path = L!("/path/to/script.txt");
    
    assert_eq!(has_shell_extension(fish_path), true);
    assert_eq!(has_shell_extension(nos_path), true);
    assert_eq!(has_shell_extension(other_path), false);
    
    assert_eq!(get_shell_extension(fish_path), Some(ShellExtension::Fish));
    assert_eq!(get_shell_extension(nos_path), Some(ShellExtension::Nos));
    assert_eq!(get_shell_extension(other_path), None);
    
    assert_eq!(
        strip_shell_extension(fish_path).map(|s| s.to_string()),
        Some("/path/to/script".into())
    );
    assert_eq!(
        strip_shell_extension(nos_path).map(|s| s.to_string()),
        Some("/path/to/script".into())
    );
    assert_eq!(strip_shell_extension(other_path), None);
}

#[test]
fn test_extension_priority() {
    // Create a temporary directory structure
    let dir = tempdir().unwrap();
    let base_path = dir.path();
    
    // Create a fish function file
    let fish_file_path = base_path.join("function.fish");
    let mut fish_file = File::create(&fish_file_path).unwrap();
    write!(fish_file, "# This is a fish function").unwrap();
    
    // Create a nos function file (should take precedence)
    let nos_file_path = base_path.join("function.nos");
    let mut nos_file = File::create(&nos_file_path).unwrap();
    write!(nos_file, "# This is a nos function").unwrap();
    
    // Convert paths to WString
    let dir_wstr = str2wcstring(base_path.to_string_lossy().as_bytes());
    let function_name = L!("function");
    
    // Test that find_file_with_any_extension finds the .nos file first
    if let Some((path, _)) = find_file_with_any_extension(&dir_wstr, function_name) {
        assert!(path.ends_with(L!("function.nos")), "Expected to find .nos file first");
    } else {
        panic!("Failed to find any function file");
    }
    
    // Now delete the .nos file and make sure it finds the .fish file
    std::fs::remove_file(nos_file_path).unwrap();
    
    if let Some((path, _)) = find_file_with_any_extension(&dir_wstr, function_name) {
        assert!(path.ends_with(L!("function.fish")), "Expected to find .fish file after removing .nos file");
    } else {
        panic!("Failed to find .fish function file");
    }
}

#[test]
fn test_config_precedence() {
    // Create temporary directory for config files
    let dir = tempdir().unwrap();
    let base_path = dir.path();
    
    // Create config.fish
    let fish_config_path = base_path.join("config.fish");
    let mut fish_config = File::create(&fish_config_path).unwrap();
    write!(fish_config, "set -g FROM_FISH_CONFIG true").unwrap();
    
    // Create nos_config.nos
    let nos_config_path = base_path.join("nos_config.nos");
    let mut nos_config = File::create(&nos_config_path).unwrap();
    write!(nos_config, "set -g FROM_NOS_CONFIG true").unwrap();
    
    // Create a parser to evaluate files
    let env = EnvStack::new();
    let parser = Parser::new(&env, fish::parser::CancelBehavior::Jump);
    
    // Simulate reading both files
    let dir_wstr = str2wcstring(base_path.to_string_lossy().as_bytes());
    
    // First fish config
    let fish_config_wstr = dir_wstr.to_owned() + L!("/config.fish");
    let fish_cmd = L!("source ").to_owned() + fish_config_wstr.as_utfstr();
    let _ = parser.eval(&fish_cmd, &fish::io::IoChain::new());
    
    // Then nos config
    let nos_config_wstr = dir_wstr.to_owned() + L!("/nos_config.nos");
    let nos_cmd = L!("source ").to_owned() + nos_config_wstr.as_utfstr();
    let _ = parser.eval(&nos_cmd, &fish::io::IoChain::new());
    
    // Check that both variables are set
    assert!(parser.vars().get(L!("FROM_FISH_CONFIG")).is_some(), "Fish config variable not set");
    assert!(parser.vars().get(L!("FROM_NOS_CONFIG")).is_some(), "Nos config variable not set");
}
