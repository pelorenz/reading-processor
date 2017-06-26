.onAttach <- function(...) {
    msg <- paste("  Dusa, Adrian (2007) User manual for the QCA(GUI) package in R.",
                 "  Journal of Business Research 60(5), 576-586.", sep="\n")
    msg <- paste(msg, "\n\nTo run the graphical user interface, use: runGUI()\n", sep="")
    if (!grepl("there is no package called", tryCatch(find.package("QCApro"), error = function(e) e))) {
        msg <- paste(msg, "\nNOTE: Found multiple function names and object type conflicts with package QCApro.",
                          "\n      To avoid confusion, please uninstall it before using this software, with:\n",
                          "      uninstall(\"QCApro\")", sep="")
    }
    packageStartupMessage("\nTo cite this package in publications, please use:\n", msg, "\n")
}
