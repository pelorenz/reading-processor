`pof` <-
function(setms, outcome, data, relation = "nec", inf.test = "",
         incl.cut = c(0.75, 0.5), ...) {
    funargs <- lapply(match.call(expand.dots = TRUE), deparse) 
    other.args <- list(...)
    conds <- ""
    condnegated <- NULL
    if (inherits(tryCatch(eval(setms), error = function(e) e), "error")) {
        setms <- funargs$setms
    }
    if (!is.character(setms)) {
        if (inherits(testit <- tryCatch(eval(setms), error = function(e) e), "error")) {
            setms <- deparse(funargs$setms)
        }
        else {
            testit <- capture.output(testit)
            if (is.character(testit) & length(testit) == 1) {
                if (grepl("~", testit)) {
                    if (eval.parent(parse(text=paste0("\"", gsub("~", "", testit), "\" %in% ls()")), n = 1)) {
                        setms <- 1 - eval.parent(parse(text=paste("get(\"", gsub("~", "", testit), "\")", sep="")), n = 1)
                        condnegated <- TRUE
                    }
                    else {
                        setms <- testit
                    }
                }
            }
        }
    }
    else {
        if (setms == tolower(setms) & setms != toupper(setms)) {
            if (eval.parent(parse(text=paste0("\"", toupper(setms), "\" %in% ls()")), n = 1)) {
                conds <- toupper(setms)
                setms <- 1 - eval.parent(parse(text=paste("get(\"", toupper(setms), "\")", sep="")), n = 1)
                condnegated <- TRUE
            }
        }
    }
    outcomename <- ""
    outnegated <- NULL
    if (inherits(tryCatch(eval(outcome), error = function(e) e), "error")) {
        outcome <- funargs$outcome
    }
    if (!is.character(outcome)) {
        if (inherits(testit <- tryCatch(eval(outcome), error = function(e) e), "error")) {
            outcome <- deparse(funargs$outcome)
        }
        else {
            testit <- capture.output(testit)
            if (is.character(testit) & length(testit) == 1) {
                if (grepl("~", testit)) {
                    if (eval.parent(parse(text=paste0("\"", gsub("~", "", testit), "\" %in% ls()")), n = 1)) {
                        outcome <- 1 - eval.parent(parse(text=paste("get(\"", gsub("~", "", testit), "\")", sep="")), n = 1)
                        condnegated <- TRUE
                    }
                    else {
                        outcome <- testit
                    }
                }
            }
        }
    }
    icp <- 0.75
    ica <- 0.5
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
        if ("incl.cut1" %in% names(other.args) & identical(icp, 0.75)) {
            icp <- other.args$incl.cut1
        }
        if ("incl.cut0" %in% names(other.args) & identical(ica, 0.5)) {
            ica <- other.args$incl.cut0
        }
    recursive <- "recursive" %in% names(other.args)
    via.eqmcc <- "via.eqmcc" %in% names(other.args)
    force.rows <- "force.rows" %in% names(other.args)
    if (is.null(outnegated)) {
        outnegated <- identical(substr(gsub("[[:space:]]", "", funargs$outcome), 1, 2), "1-")
    }
    if (is.null(condnegated)) {
        condnegated <- identical(substr(gsub("[[:space:]]", "", funargs$setms), 1, 2), "1-")
    }
    fuzzyop <- FALSE
    if (recursive) {
        mins <- other.args$mins
        outcome <- other.args$vo
        sum.outcome <- other.args$so
        pims <- other.args$pims
        incl.cov <- matrix(NA, nrow=ncol(mins), ncol=4)
    }
    else {
        outcomename <- "Y" 
        if (!missing(data)) {
            if (is.matrix(data)) {
                data <- as.data.frame(data)
            }
            verify.qca(data)
            colnames(data) <- toupper(colnames(data))
            for (i in colnames(data)) {
                if (!is.numeric(data[, i]) & possibleNumeric(data[, i])) {
                    data[, i] <- asNumeric(data[, i])
                }
            }
        }
        if (class(setms) == "character") {
            if (length(setms) == 1) {
                if (missing(data)) {
                    cat("\n")
                    stop(simpleError("The data argument is missing, with no default.\n\n"))
                }
                expression <- setms
                if (grepl("<=>", expression)) {
                    cat("\n")
                    stop(simpleError("Incorrect expression: relation can only be => or <=.\n\n"))
                }
                multivalue <- grepl("[{|}]", expression)
                conditions <- colnames(data)
                if (missing(outcome)) {
                    outcome <- ""
                }
                expression <- unlist(strsplit(expression, split = "<="))
                if (length(expression) == 1) {
                    expression <- unlist(strsplit(expression, split = "=>"))
                    if (length(expression) > 1) {
                        relation <- "suf"
                        outcome <- trimstr(expression[2])
                        expression <- trimstr(expression[1])
                    }
                }
                else {
                    outcome <- trimstr(expression[2])
                    expression <- trimstr(expression[1])
                }
                if (identical(outcome, "")) {
                    cat("\n")
                    stop(simpleError("Expression without outcome.\n\n"))
                }
                else {
                    if (is.character(outcome)) {
                        conditions <- setdiff(conditions, outcome)
                        if (! toupper(gsub("~", "", curlyBrackets(outcome, outside=TRUE))) %in% colnames(data)) {
                            cat("\n")
                            stop(simpleError("The outcome in the expression is not found in the data.\n\n"))
                        }
                    }
                }
                if (is.character(outcome)) {
                    if (substring(outcome, 1, 1) == "~") {
                        neg.out <- TRUE
                        outcome <- substring(outcome, 2)
                    }
                    if (grepl("[{|}]", outcome)) {
                        outcome.value <- curlyBrackets(outcome)
                        outcome <- curlyBrackets(outcome, outside=TRUE)
                        data[, toupper(outcome)] <- as.numeric(data[, toupper(outcome)] %in% splitstr(outcome.value))
                    }
                    else if (! outcome %in% colnames(data)) {
                        data[, toupper(outcome)] <- 1 - data[, toupper(outcome)]
                    }
                    outcome <- toupper(outcome)
                }
                complete <- FALSE
                if ("complete" %in% names(other.args)) {
                    if (is.logical(other.args$complete)) {
                        complete <- other.args$complete
                    }
                }
                if (is.character(outcome)) {
                    data2 <- data[, -which(colnames(data) == outcome)]
                    setms <- compute(expression, data2, separate = TRUE)
                    if (is.data.frame(setms)) {
                        setms$expression <- compute(expression, data2)
                    }
                    else {
                        setms <- setNames(as.data.frame(setms), expression)
                    }
                }
                else {
                    setms <- compute(expression, data, separate = TRUE)
                    if (is.data.frame(setms)) {
                        setms$expression <- compute(expression, data)
                    }
                    else {
                        setms <- setNames(as.data.frame(setms), expression)
                    }
                }
                fuzzyop <- TRUE
            }
            else {
                cat("\n")
                stop(simpleError("Only one expression allowed.\n\n"))
            }
        }
        error <- FALSE
        if (all(is.character(outcome)) & length(outcome) == 1) {
            if (missing(data)) {
                cat("\n")
                stop(simpleError("The data argument is missing, with no default.\n\n"))
            }
            else {
                outcome <- toupper(outcome)
                if (substring(outcome, 1, 1) == "~") {
                    neg.out <- TRUE
                    outcome <- substring(outcome, 2)
                }
                if (identical(substr(gsub("[[:space:]]|\"", "", funargs$outcome), 1, 2), "1-")) {
                    neg.out <- TRUE
                    outcome <- gsub("1-", "", gsub("[[:space:]]|\"", "", funargs$outcome))
                }
                if (! toupper(curlyBrackets(outcome, outside = TRUE)) %in% colnames(data)) {
                    cat("\n")
                    stop(simpleError("Inexisting outcome name.\n\n"))
                }
                if (grepl("[{|}]", outcome)) {
                    outcome.value <- curlyBrackets(outcome)
                    outcome <- curlyBrackets(outcome, outside=TRUE)
                    data[, toupper(outcome)] <- as.numeric(data[, toupper(outcome)] %in% splitstr(outcome.value))
                }
                outcomename <- toupper(outcome)
                outcome <- data[, outcomename]
            }
        }
        else if (is.vector(outcome)) {
            if (identical(outcomename, "")) {
                outcomename <- "Y"
                verify.qca(outcome)
                if (!inherits(tc <- tryCatch(getName(funargs$outcome), error = function(e) e), "error")) {
                    outcomename <- tc
                }
            }
        }
        else {
            cat("\n")
            stop(simpleError("The outcome should be either a column name in a dataset\n       or a vector of set membership values.\n\n"))
        }
        if (!(nec(relation) | suf(relation))) {
            cat("\n")
            stop(simpleError("The relationship should be either \"necessity\" or \"sufficiency\".\n\n"))
        }
        if (!missing(data)) {
            if (length(outcome) != nrow(data)) {
                cat("\n")
                stop(simpleError("The outcome's length should be the same as the number of rows in the data.\n\n"))
            }
            colnames(data) <- toupper(colnames(data))
            outcomename <- toupper(outcomename)
            conditions <- setdiff(colnames(data), outcomename)
            data <- data[, c(conditions, outcomename)]
            if (any(outcomename %in% colnames(data))) {
                noflevels <- getNoflevels(data, conditions, outcomename)$noflevels
            }
            else {
                cat("\n")
                stop(simpleError("The outcome was not found in the data.\n\n"))
            }
        }
        pims <- FALSE
        if (class(setms) == "fuzzyop") {
            conditions <- "expression"
            setms <- data.frame(X = as.vector(setms))
            colnames(setms) <- conditions
            fuzzyop <- TRUE
        }
        if (is.data.frame(setms)) {
            if (missing(outcome)) {
                cat("\n")
                stop(simpleError("Outcome is missing, with no default.\n\n"))
            }
            else {
                conditions <- colnames(setms)
                verify.qca(setms)
                for (i in conditions) {
                    if (!is.numeric(setms[, i]) & possibleNumeric(setms[, i])) {
                        setms[, i] <- asNumeric(setms[, i])
                    }
                    if (i == "expression") {
                        fuzzyop <- TRUE
                    }
                }
                if (missing(data)) { 
                    if (nrow(setms) == length(outcome)) {
                        newdata <- cbind(setms, outcome)
                        colnames(newdata)[ncol(newdata)] <- outcomename
                        pims <- TRUE
                    }
                    else {
                        cat("\n")
                        stop(simpleError("The length of outcome should be the same as the number of rows in \"setms\".\n\n"))
                    }
                }
                else {
                    if (nrow(setms) == nrow(data)) {
                        data <- cbind(setms, outcome)
                        pims <- TRUE
                    }
                    else {
                        cat("\n")
                        stop(simpleError("The number of rows in \"setms\" should be the same as the number of rows in the data.\n\n"))
                    }
                }
            }
        }
        else if (is.matrix(setms)) {
            if (via.eqmcc) {
                conditions <- other.args$conditions
            }
            if (missing(data)) {
                cat("\n")
                stop(simpleError("The data argument is missing, with no default.\n\n"))
            }
            if (ncol(setms) == length(conditions)) {
                setms[setms < 0] <- -1
                setms <- setms + 1
            }
            else {
                cat("\n")
                stop(simpleError("The number of columns in the \"setms\" does not match the number of conditions.\n\n"))
            }
        }
        else if (is.vector(setms)) {
            setms <- asNumeric(setms)
            setms <- setms[!is.na(setms)]
            if (length(setms) == 0) {
                cat("\n")
                stop(simpleError("The \"setms\" argument does not contain any numbers.\n\n"))
            }
            if (force.rows) {
                if (missing(data)) {
                    cat("\n")
                    stop(simpleError("The data argument is missing, with no default.\n\n"))
                }
                if (any(table(setms) > 1) | any(setms == 0)) {
                    cat("\n")
                    stop(simpleError("The \"setms\" argument does not appear to be a vector of row numbers.\n\n"))
                }
                setms <- getRow(noflevels + 1, setms)
            }
            else {
                if (length(setms) == length(outcome)) {
                    verify.qca(setms)
                    if (all(table(setms) == 1)) {
                        if (any(setms > 4)) {
                            cat("\n")
                            stop(simpleError("Assuming this is a vector of row numbers, data argument is missing with no default (try force.rows = TRUE).\n\n"))
                        }
                        else {
                            if (all(setms %% 1 == 0)) {
                                cat("\n")
                                stop(simpleError("Impossible to determine if the vector \"setms\" is data or row numbers.\n\n"))
                            }
                        }
                    }
                    newdata <- cbind(setms, outcome)
                    conditions <- "X" 
                    if (!inherits(tc <- tryCatch(getName(funargs$setms), error = function(e) e), "error")) {
                        conditions <- tc
                    }
                    colnames(newdata) <- c(conditions, outcomename)
                    pims <- TRUE
                }
                else {
                    if (missing(data)) {
                        cat("\n")
                        stop(simpleError("Data argument is missing, or the length of \"setms\" is not equal to the length of outcome.\n\n"))
                    }
                    else {
                        setms <- getRow(noflevels + 1, setms)
                    }
                }
            }
        }
        else {
            cat("\n")
            stop(simpleError("The \"setms\" argument is not correct.\n\n"))
        }
        if (missing(data)) {
            data <- as.data.frame(newdata)
            noflevels <- getNoflevels(data, conditions, outcomename)$noflevels
        }
        if (is.matrix(setms)) {
            if (is.null(colnames(setms))) {
                colnames(setms) <- toupper(conditions)
            }
            if (is.null(rownames(setms))) {
                use.tilde <- FALSE
                if ("use.tilde" %in% names(other.args)) {
                    rownames(setms) <- writePrimeimp(setms, uplow=all(noflevels == 2), use.tilde=other.args$use.tilde)
                }
                else {
                    rownames(setms) <- writePrimeimp(setms, uplow=all(noflevels == 2))
                }
                rownames(setms) <- gsub("NA\\*", "", rownames(setms))
            }
        }
        hastime <- logical(length(conditions))
        for (i in seq(length(conditions))) {
            if (any(data[, i] %in% c("-", "dc", "?"))) {
                hastime[i] <- TRUE
            }
        }
        if (!pims) {
            setms <- setms[, !hastime, drop=FALSE]
        }
        data[, which(hastime)] <- NULL
        conditions <- conditions[!hastime]
        if (neg.out) {
            outcome <- 1 - outcome
        }
        sum.outcome <- sum(outcome)
        if (pims) {
            mins <- setms
            if (is.vector(setms)) {
                length.expr <- 1
            }
            else {
                length.expr <- ncol(mins)
            }
            incl.cov <- matrix(NA, nrow = length.expr, ncol = 4)
        }
        else {
            fc <- apply(data[, conditions], 2, function(x) any(x < 1 & abs(x - round(x)) >= .Machine$double.eps^0.5))
            incl.cov <- matrix(NA, nrow=nrow(setms), ncol=4)
            length.expr <- nrow(setms)
            mins <- apply(setms, 1, function(e) {
                apply(data[, conditions, drop=FALSE], 1, function(v) {
                    if (any(ox <- e[fc] == 1)) {
                        v[fc][ox] <- 1 - v[fc][ox]
                    }
                    if (length(cp <- v[!fc]) > 0) {
                        v[!fc][e[!fc] != cp + 1] <- 0
                        v[!fc][e[!fc] == cp + 1] <- 1
                    }
                    return(min(v[e != 0]))
                })
            })
            if (!is.matrix(mins)) { 
                mins <- t(as.matrix(mins))
                rownames(mins) <- rownames(data)
            }
        }
    }
    if (is.vector(mins)) {
        mins <- as.data.frame(mins)
        colnames(mins) <- conditions
    }
    colnames(mins) <- gsub("[[:space:]|,]", "", colnames(mins))
    multivalue <- any(grepl("[{|}]", colnames(mins)))
    if (condnegated) {
        if (identical(conds, "")) {
            conds <- eval(parse(text = paste("attr(", gsub("1-", "", gsub("[[:space:]]", "", funargs$setms)), ", \"conditions\")")), envir=parent.frame())
        }
        if (any(grepl("[*]", colnames(mins)))) {
            rownames(incl.cov) <- gsub("[[:space:]]", "", sapply(lapply(colnames(mins), deMorgan, snames = conds, use.tilde = any(grepl("~", colnames(mins)))), function(x) {
                return(paste(x[[1]][[2]], collapse="+"))
            }))
        }
        else {
            if (is.null(conds)) {
                if ("conditions" %in% names(other.args)) {
                    conds <- other.args$conditions
                    if (length(conds) == 1 & length(colnames(mins)) > 1) {
                        conds <- splitstr(conds)
                    }
                }
                else {
                    conds <- conditions
                }
            }
            if (all(toupper(unique(unlist(strsplit(colnames(mins), split="")))) %in% toupper(conds))) {
                rownames(incl.cov) <- gsub("[[:space:]]", "", sapply(lapply(colnames(mins), deMorgan, snames = conds, use.tilde = any(grepl("~", colnames(mins)))), function(x) {
                    return(paste(x[[1]][[2]], collapse="+"))
                }))
            }
            else {
                rownames(incl.cov) <- paste("~", colnames(mins))
            }
        }     
    }
    else {
        rownames(incl.cov) <- colnames(mins)
    }
    colnames(incl.cov) <- c("incl", "PRI", "cov.r", "cov.u")
    pmins <- apply(mins, 2, pmin, outcome)
    primins <- apply(mins, 2, function(x) pmin(x, 1 - outcome, outcome))
    if (nec(relation)) {
        primins <- apply(mins, 2, function(x) pmin(x, 1 - x, outcome))
    }
    if (!is.matrix(pmins)) { 
        pmins <- t(as.matrix(pmins))
        rownames(pmins) <- rownames(mins)
        primins <- t(as.matrix(primins))
        rownames(primins) <- rownames(mins)
    }
    incl.cov[, 1] <- colSums(pmins)/colSums(mins)
    incl.cov[, 2] <- (colSums(pmins) - colSums(primins))/(colSums(mins) - colSums(primins))
    incl.cov[, 3] <- colSums(pmins)/sum.outcome
    if (nec(relation)) {
        incl.cov[, 1] <- colSums(pmins)/sum.outcome
        incl.cov[, 2] <- colSums(1 - mins)/colSums(1 - pmins)
        incl.cov[, 3] <- colSums(pmins)/colSums(mins)
    }
    maxmins <- unlist(fuzzyor(mins)) 
    inclusions <- unlist(fuzzyor(pmins))
    prisol <- pmin(maxmins, 1 - outcome, outcome)
    if (nec(relation)) {
        prisol <- pmin(maxmins, 1 - maxmins, outcome)
    }
    if (ncol(mins) > 1) {
        if (fuzzyop) {
            pmins <- pmins[, seq(ncol(pmins) - 1)]
        }
        for (i in seq(ncol(pmins))) {
            incl.cov[i, 4] <- incl.cov[i, 3] - sum(pmin(pmins[, i], fuzzyor(pmins[, -i]), outcome))/sum.outcome
        }
    }
    sol.incl <- sum(inclusions)/sum(maxmins)
    sol.pri <- (sum(inclusions) - sum(prisol))/(sum(maxmins) - sum(prisol))
    sum.cov <- sum(inclusions)/sum.outcome
    result.list <- list(incl.cov=as.data.frame(incl.cov, stringsAsFactors = FALSE), relation=relation)
    if (!pims & via.eqmcc) {
        result.list$sol.incl.cov <- c(incl=sol.incl, PRI=sol.pri, cov=sum.cov)
        result.list$pims <- as.data.frame(mins)
    }
    if ("recursive" %in% names(other.args)) {
        return(result.list)
    }
    showc <- FALSE
    if (is.character(inf.test) & length(inf.test) == 1) {
        inf.test <- splitstr(inf.test)
    }
    if (!identical(inf.test, "")) {
        verify.inf.test(inf.test, data)
    }
    if (identical(inf.test[1], "binom")) {
        statistical.testing <- TRUE
        if (length(inf.test) > 1) {
            alpha <- as.numeric(inf.test[2]) 
        }
        else {
            alpha <- 0.05
        }
        incl.cov <- as.data.frame(incl.cov, stringsAsFactors = FALSE)
        if (nec(relation)) {
            nofcases <- rep(sum.outcome, ncol(mins))
        }
        else {
            nofcases <- colSums(mins)
        }
        success <- as.vector(round(nofcases * as.numeric(incl.cov[, "incl"])))
        incl.cov$pval0 <- incl.cov$pval1 <- 0
        for (i in seq(length(success))) {
            incl.cov[i, "pval1"] <- binom.test(success[i], nofcases[i], p = icp, alternative = "greater")$p.value
            incl.cov[i, "pval0"] <- binom.test(success[i], nofcases[i], p = ica, alternative = "greater")$p.value
        }
        result.list$incl.cov <- incl.cov
    }
    if ("showc" %in% names(other.args)) {
        if (other.args$showc) {
            showc <- other.args$showc
            result.list$incl.cov <- cbind(result.list$incl.cov, cases = other.args$cases, stringsAsFactors=FALSE)
        }
    }
    if ("solution.list" %in% names(other.args)) {
        solution.list <- other.args$solution.list
        length.solution <- length(solution.list)
        individual <- vector("list", length=length.solution)
        for (i in seq(length.solution)) {
            individual[[i]] <- Recall(relation="sufficiency", recursive=TRUE, via.eqmcc=TRUE,
                                      mins=mins[, solution.list[[i]], drop=FALSE],
                                      vo=outcome, so=sum.outcome, pims=pims) 
        }
        return(structure(list(overall=result.list, individual=individual, essential=other.args$essential, pims=as.data.frame(mins), relation=relation, options=funargs[-1]), class="pof"))
    }
    else {
        if (nec(relation)) {
            cnames <- colnames(result.list$incl.cov)
            cnames[cnames == "PRI"] <- "RoN"
            colnames(result.list$incl.cov) <- cnames
        }
        result.list$options <- funargs[-1]
        result.list$options$fuzzyop <- fuzzyop
        result.list$options$relation <- relation
        return(structure(result.list, class="pof"))
    }   
}
