import java.io.BufferedReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;

/**
 * Calls cpmp's original ChangeDistillerReader (DistillerReader.main) once per
 * manifest line, inside a single JVM. Each line holds the 8 arguments of the
 * original call, separated by TAB:
 * fileA fileB csvPath project currentCommit previousCommit methodFileA methodFileB
 */
public class CDBatch {
	public static void main(String[] args) throws Exception {
		int n = 0;
		try (BufferedReader in = Files.newBufferedReader(Paths.get(args[0]), StandardCharsets.UTF_8)) {
			String line;
			while ((line = in.readLine()) != null) {
				if (line.isEmpty())
					continue;
				String[] a = line.split("\t");
				try {
					br.ufpr.com.gres.changedistiller.reader.DistillerReader.main(a);
				} catch (Throwable e) {
					System.err.println("CDERROR\t" + a[6] + "\t" + e);
				}
				if (++n % 500 == 0)
					System.err.println("progress " + n);
			}
		}
	}
}
