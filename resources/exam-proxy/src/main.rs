use std::collections::HashMap;
use std::ffi::OsStr;
use std::fs::{File, OpenOptions};
use std::io;
use std::io::prelude::*;
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};

use chrono::prelude::*;
use clap::{crate_authors, crate_version, Arg};

use log::{info, trace, warn};


const PROGRAM_NAME: &str = "examproxy";
const PROGRAM_DESC: &str = "Proxies a vulnerable application and logs the data sent to it.";

fn main() -> io::Result<()> {
    env_logger::init();

    ctrlc::set_handler(|| {
        info!("Terminating");
        std::process::exit(0);
    })
    .unwrap();

    let matches = clap::Command::new(PROGRAM_NAME)
        .version(crate_version!())
        .author(crate_authors!())
        .about(PROGRAM_DESC)
        .arg(
            Arg::new("output")
                .short('o')
                .long("output")
                .value_name("FILE")
                .help("Log to this file")
                .required(true)
                .takes_value(true),
        )
        .arg(
            Arg::new("program")
                .multiple_occurrences(true)
                .last(true)
                .required(true),
        )
        .get_matches();

    let output_file_name = matches.value_of("output").unwrap();
    let program = matches.values_of_os("program").unwrap().collect::<Vec<_>>();
    trace!("Writing to {}", output_file_name);

    let out_file = OpenOptions::new()
        .append(true)
        .create(true)
        .open(output_file_name)?;

    read_loop(&program, out_file)?;

    Ok(())
}

fn start_child<S: AsRef<OsStr>>(program: &[S]) -> io::Result<Child> {
    assert!(!program.is_empty());
    let filtered_env: HashMap<String, String> = std::env::vars()
        .filter(|&(ref k, _)| k == "TERM" || k == "LANG" || k == "PATH" || k.starts_with("LC_"))
        .collect();
    Command::new(&program[0])
        .args(&program[1..])
        .env_clear()
        .envs(&filtered_env)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
}

fn write_line(buffer: &mut impl io::Write, direction: &str, bytes: &[u8]) -> io::Result<()> {
    match std::str::from_utf8(bytes) {
        Ok(nice_str) => writeln!(
            buffer,
            "{} \"{}\"",
            direction,
            nice_str.trim_end_matches('\n')
        ),
        Err(_) => writeln!(buffer, "{} 0x{}", direction, hex::encode(bytes)),
    }
}

fn get_time() -> String {
    Local::now().to_rfc2822()
}

fn read_loop(program: &[&OsStr], log_file: File) -> io::Result<()> {
    let log_file = Arc::new(Mutex::new(log_file));
    trace!("Entering reading loop");
    let mut child = start_child(program)?;
    let mut child_stdin = child.stdin.take().unwrap();
    let stdout = child.stdout.take().unwrap();
    let mut proxy_stdout = std::io::stdout();
    let log_handle = log_file.clone();
    let _read_thread = std::thread::spawn(move || {
        let mut output_buffer = Vec::new();
        for byte in stdout.bytes() {
            let byte = byte.unwrap();
            output_buffer.push(byte);
            if byte == b'\n' {
                let mut log = log_handle.lock().unwrap();
                write_line(&mut *log, "<-", &output_buffer).unwrap();
                output_buffer.clear();
            }
            if let Err(e) = proxy_stdout.write(&[byte]) {
                    warn!("Error while writing output to student: {}", e);
                    break;
            };
            proxy_stdout.flush().unwrap();
        }
        if !output_buffer.is_empty() {
            let mut log = log_handle.lock().unwrap();
            write_line(&mut *log, "<-", &output_buffer).unwrap();
        }
        let mut log = log_handle.lock().unwrap();
        writeln!(&mut *log, "** closed output").unwrap();
        trace!("Stdout of child closed");
    });
    let log_handle = log_file.clone();
    let _write_thread = std::thread::spawn(move || {
        let stdin = std::io::stdin();
        let in_handle = stdin.lock();
        let mut log_buffer = Vec::new();
        let mut first_byte = true;
        for byte in in_handle.bytes() {
            if first_byte {
                first_byte = false;
                let mut log = log_handle.lock().unwrap();
                writeln!(&mut *log, "** First byte read at {}", get_time()).unwrap();
            }
            let byte = byte.unwrap();
            log_buffer.push(byte);
            if byte == b'\n' {
                let mut log = log_handle.lock().unwrap();
                write_line(&mut *log, "->", &log_buffer).unwrap();
                log_buffer.clear();
            }
            if let Err(e) = child_stdin.write(&[byte]) {
                warn!("Error while writing to stdin: {}", e);
                break;
            };
            child_stdin.flush().unwrap();
        }
        if !log_buffer.is_empty() {
            let mut log = log_handle.lock().unwrap();
            write_line(&mut *log, "->", &log_buffer).unwrap();
        }
        let mut log = log_handle.lock().unwrap();
        writeln!(&mut *log, "** closed input").unwrap();
        trace!("Stdin of program closed");
    });

    trace!("Waiting for child to terminate");
    let status = child.wait()?;
    let log_handle = log_file;
    let mut log = log_handle.lock().unwrap();
    writeln!(&mut *log, "** Terminated with status {}", status)?;
    trace!("Child terminated with status {}", status);
    //read_thread
    //    .join()
    //    .expect("Couldn't join read thread");
    trace!("Joined reading thread");
    //write_thread
    //    .join()
    //    .expect("Couldn't join write thread");
    trace!("Joined writing thread");
    Ok(())
}
