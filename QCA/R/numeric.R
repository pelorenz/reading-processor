`possibleNumeric` <-
function(x) {
    return(!any(is.na(suppressWarnings(as.numeric(na.omit(as.character(x)))))) & !all(is.na(x)))
}
`asNumeric` <-
function(x) {
    return(suppressWarnings(as.numeric(as.character(x))))
}
