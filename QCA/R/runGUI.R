`runGUI` <-
function(x) {
    if (missing(x)) {
        x <- system.file("gui", package="QCA")
    }
    Sys.setenv(userwd=getwd())
    runApp(x, launch.browser = TRUE)
}
