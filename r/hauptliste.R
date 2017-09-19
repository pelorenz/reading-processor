infile <- "C:\\Data\\Workspace\\reading-processor\\dicer-results\\05-hauptliste.csv"
inFrame <- read.delim(file=toString(infile), strip.white=TRUE, encoding="UTF-8")
shortNames <- inFrame[,1]
inData <- data.matrix(frame=inFrame[,2:dim(inFrame)[2]])
rownames(inData) <- shortNames

refData <- inData[,c('X03','X032','X038','X28','X565','X700','X788','X1582','VL8')]

# basic descriptive stats
round(stat.desc(refData), 3)
psych::describe(refData)

# shows which vars move together or contrary
round(cor(refData), 3)

# pca
fit <- princomp(refData, cor=TRUE)
summary(fit) # print variance accounted for 
loadings(fit) # pc loadings 
plot(fit,type="lines") # scree plot 
fit$scores # the principal components
biplot(fit)


# Deltas
infile2 <- "C:\\Data\\Workspace\\reading-processor\\dicer-results\\05-hauptliste-delta.csv"
inFrame2 <- read.delim(file=toString(infile2), strip.white=TRUE, encoding="UTF-8")
shortNames2 <- inFrame2[,1]
inData2 <- data.matrix(frame=inFrame2[,2:dim(inFrame2)[2]])
rownames(inData2) <- shortNames2

refData2 <- inData2[,c('X03','X032','X038','X28','X565','X700','X788','X1582','VL8')]

round(stat.desc(refData2), 3)
psych::describe(refData2)
