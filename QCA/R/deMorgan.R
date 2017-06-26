`deMorgan` <-
function(expression, snames = "", noflevels, use.tilde = FALSE) {
    if (class(expression) == "deMorgan") {
        expression <- paste(expression[[1]][[2]], collapse = " + ")
    }
    if (!missing(noflevels)) {
        noflevels <- splitstr(noflevels)
    }
    if (is(expression, "qca")) {
        result <- deMorganLoop(expression)
        attr(result, "snames") <- expression$tt$options$conditions
    }
    else if (is.character(expression) & length(expression) == 1) {
        star <- grepl("[*]", expression)
        initial <- expression
        if (grepl("~", expression)) {
            use.tilde <- TRUE
        }
        mv <- grepl("[{|}]", expression)
        expression <- sop(expression, snames = snames, noflevels = noflevels)
        trexp <- translate(expression, snames = snames, noflevels = noflevels)
        snames <- colnames(trexp)
        if (missing(noflevels)) {
            noflevels <- rep(2, ncol(trexp))
        }
        snoflevels <- lapply(noflevels, function(x) seq(x) - 1)
        negated <- paste(apply(trexp, 1, function(x) {
            wx <- which(x != -1) 
            x <- x[wx]
            nms <- names(x)
            x <- sapply(seq_along(x), function(i) {
                paste(setdiff(snoflevels[wx][[i]], splitstr(x[i])), collapse = ",")
            })
            if (mv) {
                return(paste("(", paste(nms, "{", x, "}", sep = "", collapse = " + "), ")", sep = ""))
            }
            else {
                nms[x == 0] <- tolower(nms[x == 0])
                return(paste("(", paste(nms, collapse = " + ", sep = ""), ")", sep = ""))
            }
        }), collapse = "")
        negated <- sop(negated, snames = snames, noflevels = noflevels)
        if (use.tilde & !mv) {
            trneg <- translate(negated, snames = snames, noflevels = noflevels)
            negated <- paste(apply(trneg, 1, function(x) {
                wx <- which(x >= 0)
                x <- x[wx]
                nms <- names(x)
                nms[x == 0] <- paste("~", nms[x == 0], sep = "")
                return(paste(nms, collapse = "*"))
            }), collapse = " + ")
        }
        if (!star) {
            negated <- gsub("[*]", "", negated)
        }
        result <- list(S1 = list(initial, negated))
    }
    return(structure(result, class = "deMorgan"))
}
`deMorganLoop` <-
function(qca.object) {
    noflevels <- qca.object$tt$noflevels
    if (qca.object$options$use.letters) {
        snames <- LETTERS[seq(length(noflevels))]
    }
    else {
        snames <- qca.object$tt$options$conditions
    }
    if ("i.sol" %in% names(qca.object)) {
        result <- vector("list", length=length(qca.object$i.sol))
        for (i in seq(length(qca.object$i.sol))) {
            names(result) <- names(qca.object$i.sol)
            result[[i]] <- lapply(qca.object$i.sol[[i]]$solution, paste, collapse = " + ")
            for (j in length(result[[i]])) {
                result[[i]][j] <- deMorgan(result[[i]][[j]], snames = snames, noflevels = noflevels)
            }
        }
    }
    else {
        result <- lapply(lapply(qca.object$solution, paste, collapse = " + "), function(x) {
            deMorgan(x, snames = snames, noflevels = noflevels)[[1]]
        })
        names(result) <- paste("S", seq(length(result)), sep="")
    }
    return(result)
}
