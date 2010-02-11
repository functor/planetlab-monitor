
source("functions.r");

ikern <- read.csv("/Users/soltesz/Downloads/out.csv", TRUE, sep=",")
f<-factor(ikern$kernel_version, sort(unique(ikern$kernel_version)), sequence(length(unique(ikern$kernel_version))))

u<-ikern$uptime/(60*60*24)

current_time <- as.numeric(format(Sys.time(), "%s"))
i<-(current_time-ikern$install_date)/(60*60*24)

plot(f,u)


sites <- read.csv("/Users/soltesz/Downloads/sites.csv", TRUE, sep=",")
f<-factor(sites$status, sort(unique(sites$status)), sequence(length(unique(sites$status))))

s<-sites$sliver_count

res <- read.csv("/Users/soltesz/Downloads/out_resources.csv", TRUE, sep=",")
library(lattice)
cloud(memsize ~ disksize * cpuspeed|numcores, data=res)

x<-c(res[2],res[4],res[5])
pairs(x)



mdrc <- read.csv("/Users/soltesz/Downloads/out_resources.csv", TRUE, sep=",")

stripchart(round(slices(mdrc)), method="jitter")
hist(round(slices(mdrc)),breaks=30)

hist(round(slices(mdrc)),breaks=30,xlim=c(0,32))
stripchart(round(slices(mdrc)), method="jitter", add=TRUE, jitter=30, at=50)


# bottom, left, top, right
par(mai=c(0,1,0.5,0.2))
hist(round(slices(mdrc)),breaks=30,xlim=c(0,32))
par(mai=c(1.0,1,0.5,0.2))
stripchart(round(slices(mdrc))-0.5, method="jitter", jitter=20, xlim=c(0,32), ylim=c(-25,25),  ylab="Raw Samples", xlab="Slice count as a function of Mem, CPU, Disk")


png("/Users/soltesz/Downloads/slices.png")
par(mfrow=c(2,1))
par(mai=c(0,1,0.5,0.2))
hist(round(slices(mdrc)),breaks=30,xlim=c(0,32), main="Distribution of Slice Count as Function of Mem, CPU, Disk")
par(mai=c(1.0,1,0.5,0.2))
stripchart(round(slices(mdrc))-0.5, method="jitter", jitter=20, xlim=c(0,32), ylim=c(-25,25),  ylab="Raw Samples", xlab="Slice count as a function of Mem, CPU, Disk for live Planetlab Machines")
dev.off()


#-----------------------

f<-slices
f<-slices_2

s2<- f(mdrc, FALSE);
mdrc$score <- s2;
df <- data.frame(mdrc);
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
	v <- f(r, TRUE);
	unique_lb$loginbase[r$loginbase] <- r$loginbase;
	unique_lb$score[r$loginbase]    <- unique_lb$score[r$loginbase]  + r$score;
}

for ( i in 1:length(mdrc$loginbase) )
{
    r <- mdrc[i,];
	v <- f(r, TRUE);
	rscore <- unique_lb$score[r$loginbase]
	unique_lb$memsize[r$loginbase]  <- unique_lb$memsize[r$loginbase]  + v[1];
	unique_lb$disksize[r$loginbase] <- unique_lb$disksize[r$loginbase]  + v[2];
	unique_lb$cpuspeed[r$loginbase] <- unique_lb$cpuspeed[r$loginbase]  + v[3];
}

df<- data.frame(unique_lb)

h<- hist(df$score, breaks=b);
bins<-max(length(h$breaks),max(h$breaks));
c<- array(0,c(bins));
d<- array(0,c(bins));
m<- array(0,c(bins));
# foreach score value, find which range it falls into, 
# then in three columns for cpu, mem, disk, record the fraction of each.
# then plot each sequence in a stacked graph, perhaps beside h$counts
for ( i in 1:length(df$cpuspeed) )
{
    r <- df[i,];
    s <- index_of_bin(h, r$score); # find bin position...
    # take fraction that each component contributes to the total, and add to sum

    m[s] <- m[s] + unique_lb$memsize[r$loginbase];
    d[s] <- d[s] + unique_lb$disksize[r$loginbase];
    c[s] <- c[s] + unique_lb$cpuspeed[r$loginbase];
}

# ----------------------
### HOSTS
# ---  get plot of contributing parts
h<- hist(df$score, breaks=b);
bins<-max(length(h$breaks),max(h$breaks));
c<- array(0,c(bins));
d<- array(0,c(bins));
m<- array(0,c(bins));
# foreach score value, find which range it falls into, 
# then in three columns for cpu, mem, disk, record the fraction of each.
# then plot each sequence in a stacked graph, perhaps beside h$counts
for ( i in 1:length(df$cpuspeed) )
{
    r <- df[i,1:6];
    s <- index_of_bin(h, r$score); # find bin position...
    # take fraction that each component contributes to the total, and add to sum
    v <- f(r, TRUE);
    m[s] <- m[s] + v[1]/r$score;
    d[s] <- d[s] + v[2]/r$score;
    c[s] <- c[s] + v[3]/r$score;
}


#a <- array(c(c,d,m), dim=c(bins, 3));
a <- array(c(c), dim=c(bins, 3));

#png("/Users/soltesz/Downloads/slice_policy_1.png")
par(mfrow=c(2,1))
par(mai=c(0.5,1,0.5,0.2))
barplot(c(0,h$counts), 
    xlab="slice count", 
    main="Distribution of Per-node 'Scores' Calculated from Mem/Disk/CPU", 
    ylab="Total Frequency", 
    ylim=c(0,160))
par(mai=c(1.0,1,0,0.2));
barplot(t(a), 
    legend=c("CPUspeed (GHz)", "DISKsize (GB)", "MEMsize (GB)"), 
    col=c("pink", "lightblue", "lightgreen"), 
    ylim=c(0,160),
    ylab="Total with Break-down",
    xlab="Per-node Score",
    names.arg=h$breaks,
);
#dev.off()



#a <- list(cpuspeed=c, memsize=m, disksize=d);
# barplot(t(a), legend=c("cpuspeed", "disksize", "memsize"), col = c("pink", "lightblue", "lightgreen"), ylab="Total Contribution by CPU, Disk, Mem ")
