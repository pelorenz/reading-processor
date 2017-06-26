`sop` <- function(expression, snames = "", noflevels, data) {
    snames <- splitstr(snames)
    multivalue <- any(grepl("[{|}]", expression))
    if (multivalue) {
        expression <- toupper(gsub("[*]", "", expression))
        verify.multivalue(expression, snames = snames, noflevels = noflevels, data = data)
    }
    getbl <- function(expression) {
        bl <- splitMainComponents(gsub("[[:space:]]", "", expression))
        bl <- splitBrackets(bl)
        bl <- removeSingleStars(bl)
        bl <- splitPluses(bl)
        bl <- splitStars(bl, "*")
        bl <- solveBrackets(bl)
        bl <- simplifyList(bl)
        return(bl)
    }
    bl <- list()
    for (i in seq(length(expression))) {
        bl <- c(bl, lapply(getbl(expression[i]), function(x) {
            x <- unlist(x)
            if (multivalue) {
                outx <- toupper(curlyBrackets(x, outside=TRUE))
                inx <- curlyBrackets(x)
                x <- paste(outx, "{", inx, "}", sep = "")
            }
            x <- cx <- unique(unlist(x))
            tx <- which(grepl("~", x))
            if (!multivalue) {
                if (any(tx)) {
                    x <- gsub("~", "", x)
                    uptx <- x[tx] %in% toupper(x)
                    lotx <- x[tx] %in% tolower(x)
                    x[tx[uptx]] <- tolower(x[tx[uptx]])
                    x[tx[lotx]] <- toupper(x[tx[lotx]])
                }
            }
            cx <- cx[!duplicated(x)]
            if (any(duplicated(toupper(gsub("~", "", cx))))) {
                return(NULL)
            }
            else {
                return(cx)
            }
        }))
    }
    bl <- unique(bl[!unlist(lapply(bl, is.null))])
    redundants <- logical(length(bl))
    if (length(bl) > 1) {
        for (i in seq(length(bl) - 1)) {
            for (j in seq(i + 1, length(bl))) {
                if (all(bl[[i]] %in% bl[[j]]) & length(bl[[i]]) < length(bl[[j]])) {
                    redundants[j] <- TRUE
                }
                if (all(bl[[j]] %in% bl[[i]]) & length(bl[[j]]) < length(bl[[i]])) {
                    redundants[i] <- TRUE
                }
            }
        }
    }
    bl <- bl[!redundants]
    if (!identical(snames, "")) {
        bl <- unique(unlist(lapply(bl, function(x) {
            paste(x[order(match(toupper(gsub("~", "", x)), toupper(snames)))], collapse = "*")
        })))
        if (any(blsn <- toupper(gsub("~", "", bl)) %in% toupper(snames))) {
            bl[blsn] <- bl[blsn][order(match(toupper(gsub("~", "", bl[blsn])), toupper(snames)))]
        }
    }
    else {
        bl <- unique(unlist(lapply(bl, paste, collapse = "*")))
    }
    if (multivalue) {
        blt <- as.vector(apply(translate(bl, snames = snames, noflevels = noflevels), 1, function(x) {
            x <- x[x >= 0]
            return(as.vector(paste(names(x), "{", x, "}", sep = "", collapse = "*")))
        }))
        if (identical(bl, blt)) {
            return(paste(bl, collapse = " + "))
        }
        return(Recall(paste(blt, collapse = " + ")))
    }
    else {
        return(paste(bl, collapse = " + "))
    }
}
