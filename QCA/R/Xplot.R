`Xplot` <- function(x, jitter = FALSE, at = NULL, ...) {
    other.args <- list(...)
    funargs <- unlist(lapply(match.call(), deparse)[-1])
    xname <- getName(funargs[1])
    linex <- 1.75
    jitfactor <- 0.5
    jitamount <- 0.5
    cexpoints <- 1
    cexaxis <- 0.8
    pch <- 21
    bgpoints <- NA
    if (length(testarg <- which(names(other.args) == "line")) > 0) {
        linex <- other.args$line
        other.args <- other.args[-testarg]
    }
    if (length(testarg <- which(names(other.args) == "factor")) > 0) {
        jitfactor <- other.args$factor
        other.args <- other.args[-testarg]
    }
    if (length(testarg <- which(names(other.args) == "amount")) > 0) {
        jitamount <- other.args$amount
        other.args <- other.args[-testarg]
    }
    if (length(testarg <- which(names(other.args) == "cex")) > 0) {
        cexpoints <- other.args$cex
        other.args <- other.args[-testarg]
    }
    if (length(testarg <- which(names(other.args) == "cex.axis")) > 0) {
        cexaxis <- other.args$cex.axis
        other.args <- other.args[-testarg]
    }
    if (length(testarg <- which(names(other.args) == "pch")) > 0) {
        pch <- other.args$pch
        other.args <- other.args[-testarg]
    }
    if (length(testarg <- which(names(other.args) == "bg")) > 0) {
        bgpoints <- other.args$bg
        other.args <- other.args[-testarg]
    }
    if (length(testarg <- which(names(other.args) == "xlab")) > 0) {
        xname <- other.args$xlab
        other.args <- other.args[-testarg]
    }
    y <- rep(1, length(x))
    if (jitter) {
        y <- jitter(y, jitfactor, jitamount)
    }
    toplot <- list(as.name("plot"), x, y)
    toplot$type <- "n"
    if (!is.null(at)) {
        toplot$xlim <- range(at)
    }
    toplot$ylim <- c(0, 2)
    toplot$xlab <- ""
    toplot$ylab <- ""
    toplot$axes <- FALSE
    if (length(other.args) > 0) {
        toplot <- c(toplot, other.args)
    }
    par(mar = c(ifelse(xname == "", 2, 3), 0.3, 0, 0))
    suppressWarnings(eval(as.call(toplot)))
    axis(1, at = at, cex.axis = cexaxis)
    title(xlab = xname, cex.lab = cexaxis + 0.1, font.lab = 2, line = linex)
    plotpoints <- list(as.name("points"), x, y, pch = pch, cex = cexpoints, bg = bgpoints)
    suppressWarnings(eval(as.call(c(plotpoints, other.args))))
}
