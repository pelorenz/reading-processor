`translate` <-
function(expression = "", snames = "", noflevels, data, ...) {
    if (!missing(noflevels)) {
        noflevels <- splitstr(noflevels)
    }
    if (identical(expression, "")) {
        cat("\n")
        stop(simpleError("Empty expression.\n\n"))
    }
    if (any(grepl("<=>", expression)) |
        any(grepl("=>", expression))  | 
        any(grepl("<=", expression))) {
        cat("\n")
        stop(simpleError("Incorrect expression.\n\n"))
    }
    if (!is.vector(snames)) {
        cat("\n")
        stop(simpleError("Set names should be a single string or a vector of names.\n\n"))
    }
    other.args <- list(...)
    tomatrix <- TRUE
    if ("tomatrix" %in% names(other.args)) {
        tomatrix <- other.args$tomatrix
    }
    if (identical(snames, "")) {
        if (!missing(data)) {
            snames <- colnames(data)
        }
    }
    else { 
        snames <- toupper(splitstr(snames))
    }
    if (any(grepl(",", gsub(",[0-9]", "", expression)))) {
        expression <- splitstr(expression)
    }
    expression <- unlist(lapply(expression, function(x) {
        if (grepl("[(|)]", x)) {
            x <- sop(x, snames = snames, noflevels = noflevels, data = data)
        }
        return(x)
    }))
    pporig <- trimstr(unlist(strsplit(expression, split="[+]")))
    multivalue <- any(grepl("[{|}]", expression))
    expression <- gsub("[[:space:]]", "", expression)
    if (multivalue) {
        expression <- gsub("[*]", "", expression)
        expression <- toupper(expression)
        verify.multivalue(expression, snames = snames, noflevels = noflevels, data = data)
        pp <- unlist(strsplit(expression, split="[+]"))
        conds <- sort(unique(toupper(gsub("~", "", curlyBrackets(pp, outside=TRUE)))))
        if (identical(snames, "")) {
            if (!missing(data)) {
                    conds <- intersect(colnames(data), conds)
            }
        }
        else {
            if (all(conds %in% snames)) {
                conds <- snames
            }
            else {
                cat("\n")
                stop(simpleError("Parts of the expression don't match the set names from \"snames\" argument.\n\n"))
            }
        }
        if (any(grepl("~", expression))) {
            if (missing(noflevels)) {
                noflevels <- getNoflevels(data, conds)$noflevels
            }
        }
        retlist <- lapply(pp, function(x) {
            outx <- toupper(curlyBrackets(x, outside=TRUE))
            inx <- lapply(curlyBrackets(x), splitstr)
            notilde <- gsub("~", "", outx)
            tbl <- table(notilde)
            dupnot <- duplicated(notilde)
            if (length(win <- which(grepl("~", outx))) > 0) {
                for (i in win) {
                    inx[[i]] <- setdiff(seq(noflevels[which(conds %in% notilde[i])]) - 1, inx[[i]])
                }
            }
            empty <- FALSE
            for (i in seq(length(conds))) {
                if (conds[i] %in% notilde[dupnot]) { 
                    wdup <- which(notilde == conds[i])
                    inx[[wdup[1]]] <- intersect(inx[[wdup[1]]], inx[[wdup[2]]])
                    if (length(wdup) > 2) {
                        for (i in seq(3, length(wdup))) {
                            dupres <- intersect(dupres, inx[[wdup[i]]])
                        }
                    }
                    if (length(inx[[wdup[1]]]) == 0) {
                        empty <- TRUE
                    }
                }
            }
            ret <- as.list(rep(-1, length(conds)))
            names(ret) <- conds
            ret[gsub("~", "", outx[!dupnot])] <- inx[!dupnot]
            return(ret)
        })
        names(retlist) <- pporig
    }
    else {
        pp <- unlist(strsplit(expression, split="[+]"))
        if (any(grepl("[*]", expression))) {
            conds <- sort(unique(toupper(gsub("~", "", unlist(strsplit(pp, split="[*]"))))))
            if (!identical(snames, "")) {
                if (all(conds %in% snames)) {
                    conds <- snames
                }
                else {
                    cat("\n")
                    stop(simpleError("Parts of the expression don't match the set names from \"snames\" argument.\n\n"))
                }
            }
            retlist <- lapply(pp, function(x) {
                x <- unlist(strsplit(x, split="[*]"))
                inx <- lapply(x, function(x) as.numeric(identical(x, toupper(x))))
                notilde <- toupper(gsub("~", "", x))
                tbl <- table(notilde)
                dupnot <- duplicated(notilde)
                if (length(win <- which(grepl("~", x))) > 0) {
                    for (i in win) {
                        inx[[i]] <- 1 - inx[[i]]
                    }
                }
                empty <- FALSE
                for (i in seq(length(conds))) {
                    if (conds[i] %in% notilde[dupnot]) { 
                        if (length(unique(unlist(inx[which(notilde == conds[i])]))) > 1) {
                            empty <- TRUE
                        }
                    }
                }
                ret <- as.list(rep(-1, length(conds)))
                names(ret) <- conds
                if (!empty) {
                    ret[toupper(gsub("~", "", x[!dupnot]))] <- inx[!dupnot]
                }
                return(ret)
            })
            names(retlist) <- pporig
        }
        else {
            conds <- sort(unique(toupper(gsub("~", "", pp))))
            if (all(nchar(conds) == 1)) {
                if (!identical(snames, "")) {
                    if (all(conds %in% snames)) {
                        conds <- snames
                    }
                    else {
                        cat("\n")
                        stop(simpleError("Parts of the expression don't match the set names from \"snames\" argument.\n\n"))
                    }
                }
                retlist <- lapply(pp, function(x) {
                    inx <- as.numeric(identical(x, toupper(x)))
                    if (grepl("~", x)) {
                        inx <- 1 - x
                    }
                    ret <- as.list(rep(-1, length(conds)))
                    names(ret) <- conds
                    ret[[toupper(gsub("~", "", x))]] <- inx
                    return(ret)
                })
                names(retlist) <- pporig
            }
            else {
                if (identical(snames, "")) {
                    snames <- sort(unique(toupper(unlist(strsplit(gsub("~", "", pp), split = "")))))
                }
                    conds <- snames
                if (all(toupper(gsub("~", "", pp)) %in% snames)) {
                    retlist <- lapply(pp, function(x) {
                        inx <- as.numeric(identical(x, toupper(x)))
                        if (grepl("~", x)) {
                            inx <- 1 - inx
                        }
                        ret <- as.list(rep(-1, length(conds)))
                        names(ret) <- conds
                        ret[[toupper(gsub("~", "", x))]] <- inx
                        return(ret)
                    })
                    names(retlist) <- pporig
                }
                else {
                    if (all(nchar(snames) == 1)) {
                        retlist <- lapply(pp, function(x) {
                            x <- unlist(strsplit(x, split=""))
                            if (any(x == "~")) {
                                y <- which(x == "~")
                                if (max(y) == length(x)) {
                                    cat("\n")
                                    stop(simpleError("Incorrect expression, tilde not in place.\n\n"))
                                }
                                x[y + 1] <- paste("~", x[y + 1], sep="")
                                x <- x[-y]
                            }
                            inx <- lapply(x, function(x) as.numeric(identical(x, toupper(x))))
                            notilde <- toupper(gsub("~", "", x))
                            tbl <- table(notilde)
                            dupnot <- duplicated(notilde)
                            if (length(win <- which(grepl("~", x))) > 0) {
                                for (i in win) {
                                    inx[[i]] <- 1 - inx[[i]]
                                }
                            }
                            empty <- FALSE
                            for (i in seq(length(conds))) {
                                if (conds[i] %in% notilde[dupnot]) { 
                                    if (length(unique(unlist(inx[which(notilde == conds[i])]))) > 1) {
                                        empty <- TRUE
                                    }
                                }
                            }
                            ret <- as.list(rep(-1, length(conds)))
                            names(ret) <- conds
                            if (!empty) {
                                ret[toupper(gsub("~", "", x[!dupnot]))] <- inx[!dupnot]
                            }
                            return(ret)
                        })
                        names(retlist) <- pporig
                    }
                    else {
                        perms <- function(x) {
                            if (length(x) == 1) {
                                return(x)
                            }
                            else {
                                res <- matrix(nrow = 0, ncol = length(x))
                                for(i in seq_along(x)) {
                                    res <- rbind(res, cbind(x[i], Recall(x[-i])))
                                }
                                return(res)
                            }
                        }
                        snames <- snames[unlist(lapply(snames, grepl, toupper(expression)))]
                        if (length(snames) > 7) {
                            cat("\n")
                            stop(simpleError("Too many causal snames' to search.\n\n"))
                        }
                        im <- createMatrix(rep(3, length(snames)))[-1, , drop = FALSE]
                        mns <- matrix(nrow = 0, ncol = ncol(im))
                        noflevels <- rep(3, length(snames))
                        mns <- lapply(seq(2, 3^length(snames)), function(sn) {
                            sn <- getRow(noflevels, sn)
                            snames[sn == 1] <- tolower(snames[sn == 1])
                            snames <- snames[sn > 0]
                            if (length(snames) > 1) {
                                return(perms(snames))
                            }
                            else {
                                return(matrix(snames, 1, 1))
                            }
                        })
                        namespace <- unlist(lapply(mns, function(x) apply(x, 1, paste, collapse = "")))
                        if (any(duplicated(namespace))) {
                            cat("\n")
                            stop(simpleError("Impossible to translate: set names clash.\n\n"))
                        }
                        names(namespace) <- unlist(lapply(seq(length(mns)), function(x) paste(x, seq(nrow(mns[[x]])), sep = "_")))
                        matched <- match(gsub("~", "", pp), namespace)
                        if (any(is.na(matched))) {
                            cat("\n")
                            stop(simpleError("Incorrect expression, unknown set names (try using * for products).\n\n"))
                        }
                        matched <- names(namespace)[matched]
                        retlist <- lapply(seq(length(matched)), function(x) {    
                            ret <- as.list(rep(-1, length(conds)))
                            names(ret) <- conds
                            mx <- as.numeric(unlist(strsplit(matched[x], split="_")))
                            mx <- mns[[mx[1]]][mx[2], ]
                            inx <- lapply(mx, function(y) {
                                neg <- grepl(paste0("~", y), pp[x])
                                y <- as.numeric(identical(y, toupper(y)))
                                return(ifelse(neg, 1 - y, y))
                            })
                            ret[toupper(mx)] <- inx
                            return(ret)
                        })
                        names(retlist) <- pporig
                    } 
                } 
            } 
        } 
    } 
    retlist <- retlist[!unlist(lapply(retlist, function(x) all(unlist(x) < 0)))]
    if (tomatrix) {
        retlist <- do.call("rbind", lapply(retlist, function(x) {
            xnames <- names(x)
            x <- unlist(lapply(x, paste, collapse = ","))
            names(x) <- xnames
            return(x)
        }))
    }
    if (length(retlist) == 0) {
        cat("\n")
        stop(simpleError("Impossible to translate an empty set.\n\n"))
    }
    return(structure(retlist, class = "translate"))
}
