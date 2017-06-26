`createMatrix` <-
function(noflevels, ...) {
    other.args <- list(...)
    RAM <- 2
    if ("RAM" %in% names(other.args)) {
        if (length(other.args$RAM) == 1) {
            if (is.numeric(other.args$RAM) & other.args$RAM > 0) {
                RAM <- other.args$RAM
            }
        }
    }
    arrange <- FALSE
    if ("arrange" %in% names(other.args)) {
        arrange <- other.args$arrange
    }
    depth <- length(noflevels)
    if ("depth" %in% names(other.args)) {
        if (!is.null(other.args$depth)) {
            if (is.numeric(other.args$depth)) {
                depth <- other.args$depth
            }
        }
    }
    if (any(abs(noflevels) %% 1 > .Machine$double.eps ^ 0.5)) {
        cat("\n")
        stop(simpleError("The number of levels need to be integers."))
    }
    if (!is.logical(arrange)) {
        cat("\n")
        stop(simpleError("The number of \"arrange\" should be logical."))
    }
    if (abs(depth) %% 1 > .Machine$double.eps ^ 0.5) {
        cat("\n")
        stop(simpleError("The argument depth has to be an integer number."))
    }
    if ((mem <- prod(noflevels)*length(levels)*8/1024^3) > RAM) {
        cat("\n")
        stop(simpleError(paste("Too much memory needed (", round(mem, 1), " Gb) to create the matrix.", sep="")))
    }
    noflevels <- as.integer(abs(noflevels))
    arrange <- as.integer(arrange * 1)
    depth <- as.integer(abs(depth))
    nofconds <- as.integer(length(noflevels))
    if (arrange) {
        if (depth < 1 | depth > nofconds) {
            depth <- nofconds
        }
    }
    return(.Call("createMatrix", noflevels, arrange, depth, PACKAGE = "QCA"))
    pwr <- unique(noflevels)
    if (length(pwr) == 1) {
        create <- function(idx) {
            rep.int(c(sapply(seq_len(pwr) - 1, function(x) rep.int(x, pwr^(idx - 1)))),
                    pwr^nofconds/pwr^idx)
        }
        retmat <- sapply(rev(seq_len(nofconds)), create)
    }
    else {
        mbase <- c(rev(cumprod(rev(noflevels))), 1)[-1]
        orep  <- cumprod(rev(c(rev(noflevels)[-1], 1)))
        retmat <- sapply(seq_len(nofconds), function(x) {
           rep.int(rep.int(seq_len(noflevels[x]) - 1, rep.int(mbase[x], noflevels[x])), orep[x])
        })
    }
    if (is.vector(retmat)) {
        retmat <- matrix(retmat, nrow=1)
    }
    return(retmat)
}
