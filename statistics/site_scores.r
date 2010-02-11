
source("functions.r");

#system("../nodequery.py --nodelist > ../nodelist.txt")
#system("../comonquery.py --cache --nodelist ../nodelist.txt --select 'resptime>0' --fields='name,cpuspeed,numcores,memsize,disksize,bwlimit' | grep -v null | ./hn2lb.py | ./hn2pcustatus.py > ./out_resources.csv ")

mdrc <- read.csv("out_resources.csv", TRUE, sep=",")

# replace all weird numbers with defaults of 100mbps 
mdrc$bwlimit <- replace(mdrc$bwlimit, which(mdrc$bwlimit==0 | mdrc$bwlimit==1), 100000)

f<-slices_2

s2<- f(mdrc, FALSE);
mdrc$score <- s2;
b<-30;

# ----------------------
### LOGINBASE
unique_loginbase_length <- length(unique(mdrc$loginbase));
unique_lb <- list(loginbase=array(0,c(unique_loginbase_length)), 
				  score=array(0,c(unique_loginbase_length)),
				  memsize=array(0,c(unique_loginbase_length)),
				  disksize=array(0,c(unique_loginbase_length)),
				  cpuspeed=array(0,c(unique_loginbase_length))
			  )

for ( i in 1:length(mdrc$loginbase) )
{
    r <- mdrc[i,];
	unique_lb$loginbase[r$loginbase] <- r$loginbase;
	unique_lb$score[r$loginbase]	 <- unique_lb$score[r$loginbase] + r$score;

	v <- f(r, TRUE);
	unique_lb$memsize[r$loginbase]  <- unique_lb$memsize[r$loginbase]  + v[1];
	unique_lb$disksize[r$loginbase] <- unique_lb$disksize[r$loginbase]  + v[2];
	unique_lb$cpuspeed[r$loginbase] <- unique_lb$cpuspeed[r$loginbase]  + v[3];
}

df<- data.frame(unique_lb)

h<- hist(df$score, breaks=b);
bins<-length(h$breaks);
c<- array(0,c(bins));
d<- array(0,c(bins));
m<- array(0,c(bins));
b<- array(0,c(bins));
# foreach score value, find which range it falls into, 
# then in three columns for cpu, mem, disk, record the fraction of each.
# then plot each sequence in a stacked graph, perhaps beside h$counts
for ( i in 1:length(df$cpuspeed) )
{
    r <- df[i,];
    s <- index_of_bin(h, r$score); # find bin position...
    # take fraction that each component contributes to the total, and add to sum

    m[s] <- m[s] + unique_lb$memsize[r$loginbase]/r$score;
    d[s] <- d[s] + unique_lb$disksize[r$loginbase]/r$score;
    c[s] <- c[s] + unique_lb$cpuspeed[r$loginbase]/r$score;
}

a <- array(c(c,d,m), dim=c(bins, 3));

png("/Users/soltesz/Downloads/slice_policy_3.png")
par(mfrow=c(2,1))
par(mai=c(0.5,1,0.5,0.2))
barplot(c(0,h$counts), 
    xlab="slice count", 
    main="Distribution of Site Scores", 
    ylab="Total Frequency", 
    ylim=c(0,70))
par(mai=c(1.0,1,0,0.2));
barplot(t(a), 
    legend=c("CPUspeed (GHz)", "DISKsize (GB)", "MEMsize (GB)"), 
    col=c("pink", "lightblue", "lightgreen"), 
    ylim=c(0,70),
    ylab="Break-down by Resource",
    xlab="Site Score",
    names.arg=c(0,h$breaks[1:length(h$breaks)-1]),
);
dev.off()


