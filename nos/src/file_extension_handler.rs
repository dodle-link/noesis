// file_extension_handler.rs - Handling for dual file extensions
//
// Copyright (c) 2025 Napol Thanarangkaun (Noesis Open Shell)
//
// This module provides an abstraction layer for handling different file extensions 
// in the nos shell. It allows seamlessly supporting both .fish and .nos files,
// with .nos files taking precedence when both exist for the same command.

use crate::wchar::{wstr, WString, L};
use crate::wutil::{file_id_for_path, FileId, INVALID_FILE_ID};
use std::path::Path;

/// File extensions supported by the shell
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ShellExtension {
    Fish,
    Nos,
}

impl ShellExtension {
    /// Convert the extension enum to a string slice
    pub fn as_str(&self) -> &'static str {
        match self {
            ShellExtension::Fish => ".fish",
            ShellExtension::Nos => ".nos",
        }
    }
    
    /// Convert the extension enum to a wide string
    pub fn as_wstr(&self) -> &'static wstr {
        match self {
            ShellExtension::Fish => L!(".fish"),
            ShellExtension::Nos => L!(".nos"),
        }
    }
    
    /// Get all supported extensions in priority order (highest priority first)
    pub fn all_extensions() -> &'static [ShellExtension] {
        &[ShellExtension::Nos, ShellExtension::Fish]
    }
}

/// Try to locate a file with any of the supported extensions.
/// Returns the first file found, following the priority order in ShellExtension::all_extensions().
pub fn find_file_with_any_extension(base_path: &wstr, file_name: &wstr) -> Option<(WString, FileId)> {
    for ext in ShellExtension::all_extensions() {
        let mut path = base_path.to_owned();
        path.push('/');
        path.push_utfstr(file_name);
        path.push_utfstr(ext.as_wstr());
        
        let file_id = file_id_for_path(&path);
        if file_id != INVALID_FILE_ID {
            return Some((path, file_id));
        }
    }
    None
}

/// Check if a path has one of our supported extensions
pub fn has_shell_extension(path: &wstr) -> bool {
    for ext in ShellExtension::all_extensions() {
        if path.ends_with(ext.as_wstr()) {
            return true;
        }
    }
    false
}

/// Get the base name without the extension
pub fn strip_shell_extension(path: &wstr) -> Option<&wstr> {
    for ext in ShellExtension::all_extensions() {
        if let Some(base) = path.strip_suffix(ext.as_wstr()) {
            return Some(base);
        }
    }
    None
}

/// Get the file extension as ShellExtension enum
pub fn get_shell_extension(path: &wstr) -> Option<ShellExtension> {
    if path.ends_with(L!(".fish")) {
        Some(ShellExtension::Fish)
    } else if path.ends_with(L!(".nos")) {
        Some(ShellExtension::Nos)
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tests::prelude::*;
    
    #[test]
    fn test_extension_detection() {
        let fish_path = WString::from_str("test.fish");
        let nos_path = WString::from_str("test.nos");
        let other_path = WString::from_str("test.txt");
        
        assert_eq!(get_shell_extension(&fish_path), Some(ShellExtension::Fish));
        assert_eq!(get_shell_extension(&nos_path), Some(ShellExtension::Nos));
        assert_eq!(get_shell_extension(&other_path), None);
    }
    
    #[test]
    fn test_strip_extension() {
        let fish_path = WString::from_str("test.fish");
        let nos_path = WString::from_str("test.nos");
        let other_path = WString::from_str("test.txt");
        
        assert_eq!(strip_shell_extension(&fish_path).map(|s| s.to_string()), Some("test".to_string()));
        assert_eq!(strip_shell_extension(&nos_path).map(|s| s.to_string()), Some("test".to_string()));
        assert_eq!(strip_shell_extension(&other_path), None);
    }
}
