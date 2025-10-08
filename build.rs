fn main() {
    // Only compile the Windows resource on Windows
    #[cfg(windows)]
    {
        let mut res = winres::WindowsResource::new();
        res.set_icon("icons/icon.ico");
        res.compile().unwrap();
    }
}

