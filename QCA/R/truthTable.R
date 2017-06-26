`truthTable` <-
function(data, outcome = "", conditions = "", n.cut = 1,
         incl.cut = 1, complete = FALSE, show.cases = FALSE,
         sort.by = "", use.letters = FALSE, inf.test = "", ...) {
    metacall <- match.call(expand.dots = TRUE)
    other.args <- list(...)
    ica <- 1
    if (is.character(incl.cut) & length(incl.cut) == 1) {
        incl.cut <- splitstr(incl.cut)
    }
    icp <- incl.cut[1]
    if (length(incl.cut) > 1) {
        ica <- incl.cut[2]
    }
        neg.out <- FALSE
        if ("neg.out" %in% names(other.args)) {
            neg.out <- other.args$neg.out
        }
        if ("incl.cut1" %in% names(other.args) & identical(icp, 1)) {
            icp <- other.args$incl.cut1
            incl.cut[1] <- icp
        }
        if ("incl.cut0" %in% names(other.args) & identical(ica, 1)) {
            ica <- other.args$incl.cut0
            incl.cut[2] <- ica
        }
    initialcols <- colnames(data)
    colnames(data) <- toupper(colnames(data))
    conditions <- toupper(conditions)
    outcome <- toupper(outcome)
    if (length(outcome) > 1) {
        cat("\n")
        stop(simpleError("Only one outcome is allowed.\n\n"))
    }
    outcome.copy <- outcome
    initial.data <- data
    if (substring(outcome, 1, 1) == "~") {
        neg.out <- TRUE
        outcome <- substring(outcome, 2)
    }
    if (!identical(outcome, "")) {
        if (! toupper(curlyBrackets(outcome, outside=TRUE)) %in% colnames(data)) {
            cat("\n")
            stop(simpleError("Inexisting outcome name.\n\n"))
        }
    }
    if (grepl("[{|}]", outcome)) {
        outcome.value <- curlyBrackets(outcome)
        outcome <- curlyBrackets(outcome, outside=TRUE)
        data[, toupper(outcome)] <- as.numeric(data[, toupper(outcome)] %in% splitstr(outcome.value))
    }
    if (identical(conditions, "")) {
        conditions <- setdiff(names(data), outcome)
    }
    else {
        if (is.character(conditions) & length(conditions) == 1) {
            conditions <- splitstr(conditions)
        }
    }
    if (is.character(sort.by) & length(sort.by) == 1 & !identical(sort.by, "")) {
        sort.by <- splitstr(sort.by)
    }
    decreasing <- TRUE 
    if ("decreasing" %in% names(other.args)) {
        decreasing <- other.args$decreasing
    }
    if (is.character(decreasing) & length(decreasing) == 1) {
        decreasing <- splitstr(decreasing)
    }
    if (!identical(inf.test, "")) {
        inf.test <- splitstr(inf.test)
    }
    verify.tt(data, outcome, conditions, complete, show.cases, icp, ica, inf.test)
    data <- data[, c(conditions, outcome)]
    if (ica > icp) {
        ica <- icp
    }
    colnames(data) <- toupper(colnames(data))
    conditions <- toupper(conditions)
    outcome <- toupper(outcome)
    if (neg.out) {
        data[, outcome] <- 1 - data[, outcome]
    }
    nofconditions <- length(conditions)
    getnofl <- getNoflevels(data, conditions, outcome)
    data <- getnofl$data
    fuzzy.cc <- getnofl$fuzzy.cc
    noflevels <- getnofl$noflevels
    dc.code <- getnofl$dc.code
    rownames(data) <- rownames(initial.data)
    condata <- data[, conditions, drop = FALSE]
    if (any(fuzzy.cc)) {
        condata[, fuzzy.cc] <- lapply(condata[, fuzzy.cc, drop = FALSE], function(x) as.numeric(x > 0.5))
    }
    line.data <- as.vector(as.matrix(condata) %*% c(rev(cumprod(rev(noflevels))), 1)[-1])
    condata <- condata[order(line.data), ]
    uniq <- which(!duplicated(condata))
    tt <- condata[uniq, ]
    rownstt <- sort(line.data)[uniq] + 1
    rownames(tt) <- rownstt
    ipc <- .Call("truthTable", as.matrix(data[, conditions]), as.matrix(tt), as.numeric(fuzzy.cc), data[, outcome], PACKAGE="QCA")
    colnames(ipc) <- rownstt
    minmat <- ipc[seq(4, nrow(ipc)), ]
    ipc <- ipc[1:3, ]
    rownames(minmat) <- rownames(data)
    rownames(ipc) <- c("n", "incl", "PRI")
    exclude <- ipc[1, ] < n.cut
    if (sum(!exclude) == 0) {
        cat("\n")
        stop(simpleError("There are no combinations at this frequency cutoff.\n\n"))
    }
    tt$OUT <- "?"
    tt$OUT[!exclude] <- as.numeric(ipc[2, !exclude] >= (icp - .Machine$double.eps ^ 0.5))
    tt$OUT[ipc[2, !exclude] < icp & ipc[2, !exclude] >= (ica - .Machine$double.eps ^ 0.5)] <- "C"
    tt <- cbind(tt, t(ipc))
    cases <- sapply(sort(unique(line.data)), function(x) {
        paste(rownames(data)[which(line.data == x)], collapse=",")
    })
    casesexcl <- cases[exclude]
    rownstt <- rownstt[!exclude]
    cases <- cases[!exclude]
    excluded <- tt[exclude, , drop = FALSE]
    excluded$OUT <- as.numeric(ipc[2, exclude] >= (icp - .Machine$double.eps ^ 0.5))
    excluded$OUT[ipc[2, exclude] < icp & ipc[2, exclude] >= (ica - .Machine$double.eps ^ 0.5)]  <- "C"
    if (length(conditions) < 8) {
        ttc <- as.data.frame(matrix(nrow = prod(noflevels), ncol = ncol(tt)))
        colnames(ttc) <- colnames(tt)
        ttc[, seq(length(conditions))] <- createMatrix(noflevels)
        ttc$OUT   <- "?"
        ttc$n     <-  0
        ttc$incl  <- "-"
        whichpri <- which(colnames(ttc) == "PRI")
        ttc[, whichpri[length(whichpri)]] <- "-"  
        ttc[rownames(tt), ] <- tt
        tt <- ttc
    }
    if (!identical(sort.by, "")) {
        if (is.logical(sort.by)) { 
            decreasing <- as.vector(sort.by)
            sort.by <- names(sort.by)
        }
        else {
            if (missing(decreasing)) {
                decreasing <- rep(TRUE, length(sort.by))
            }
            else {
                if (is.logical(decreasing)) {
                    if (length(decreasing) == 1) {
                        decreasing <- rep(decreasing, length(sort.by))
                    }
                    else if (length(decreasing) < length(sort.by)) {
                        decreasing <- c(decreasing, rep(TRUE, length(sort.by) - length(decreasing)))
                    }
                }
                else {
                    decreasing <- rep(TRUE, length(sort.by))
                }
            }
        }
        sort.by[sort.by == "out"] <- "OUT"
        decreasing <- decreasing[sort.by %in% names(tt)]
        sort.by <- sort.by[sort.by %in% names(tt)]
        rowsorder <- seq_len(nrow(tt))
        for (i in rev(seq(length(sort.by)))) {
            rowsorder <- rowsorder[order(tt[rowsorder, sort.by[i]], decreasing = decreasing[i])]
        }
        sortvector <- rep(1, nrow(tt))
        sortvector[tt[rowsorder, "OUT"] == "?"] <- 2
        rowsorder <- rowsorder[order(sortvector)]
    }
    uppercols <- toupper(colnames(initial.data))
    for (i in seq(length(conditions))) {
        if (!fuzzy.cc[i]) {
            if (any(initial.data[, match(conditions[i], uppercols)] == dc.code)) {
                tt[, i][tt[, i] == max(tt[, i])] <- dc.code
                data[, i][data[, i] == max(data[, i])] <- dc.code
                noflevels[i] <- noflevels[i] - 1
            }
        }
    }
    statistical.testing <- FALSE
    if (inf.test[1] == "binom") {
        statistical.testing <- TRUE
        if (length(inf.test) > 1) {
            alpha <- as.numeric(inf.test[2]) 
        }
        else {
            alpha <- 0.05
        }
        observed <- which(tt$OUT != "?")
        success <- round(tt[observed, "n"] * as.numeric(tt[observed, "incl"]))
        tt$pval1 <- "-"
        if (length(incl.cut) > 1) {
            tt$pval0 <- "-"
        }
        tt[observed, "OUT"] <- 0
        for (i in seq(length(observed))) {
            pval1 <- tt[observed[i], "pval1"] <- binom.test(success[i], tt[observed[i], "n"], p = icp, alternative = "greater")$p.value
            if (length(incl.cut) > 1) {
                pval0 <- tt[observed[i], "pval0"] <- binom.test(success[i], tt[observed[i], "n"], p = ica, alternative = "greater")$p.value
            }
            if (pval1 < alpha) {
                tt[observed[i], "OUT"] <- 1
            }
            else if (length(incl.cut) > 1) {
                if (pval0 < alpha) {
                    tt[observed[i], "OUT"] <- "C"
                }
            }
        }
    }
        tt$cases <- ""
        if (length(conditions) < 8) {
            tt$cases[rownstt] <- cases
        }
        else {
            tt$cases <- cases
        }
    numerics <- unlist(lapply(initial.data, possibleNumeric))
    colnames(initial.data)[!numerics] <- initialcols[!numerics]
    x <- list(tt = tt, indexes = rownstt, noflevels = as.vector(noflevels),
              initial.data = initial.data, recoded.data = data, cases = cases, minmat = minmat,
              options = list(outcome = outcome.copy, conditions = conditions, neg.out = neg.out, n.cut = n.cut,
                             incl.cut = incl.cut, complete = complete, show.cases = show.cases,
                             use.letters = use.letters, inf.test = statistical.testing))
    if (any(exclude)) {
        excluded$cases <- ""
        excluded$cases <- casesexcl
        x$excluded <- structure(list(tt = excluded,
                                     options = list(show.cases = TRUE, complete = FALSE, excluded = TRUE)), class="tt")
    }
    if (use.letters & any(nchar(conditions) > 1)) { 
        colnames(x$tt)[seq(nofconditions)] <- LETTERS[seq(nofconditions)]
    }
    if (!identical(sort.by, "")) {
        x$rowsorder <- rowsorder
    }
    x$origin <- "QCAGUI"
    x$call <- metacall
    return(structure(x, class="tt"))
}
