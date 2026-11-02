import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import com.github.javaparser.ParserConfiguration;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.Parameter;
import com.github.javaparser.ast.body.TypeDeclaration;
import com.github.javaparser.ast.expr.ObjectCreationExpr;
import com.github.javaparser.ast.stmt.LocalClassDeclarationStmt;
import com.github.javaparser.ast.stmt.LocalRecordDeclarationStmt;

/**
 * Batch version of cpmp's JMethodsExtractor (br.ufpr.gres): same extraction
 * (StaticJavaParser, MethodDeclaration, signature and ae.toString()), but
 * processes many files in a single JVM and also writes out the chain of
 * declaring types, which is needed for the join with CK/Understand.
 *
 * Usage: java -cp <JMethodsExtractor jar>;. MethodsBatch manifest.tsv out.jsonl
 * manifest: one line per file: id \t path
 * out: one JSON line per file: {"id":..,"ok":..,"error":..,"methods":[..]}
 */
public class MethodsBatch {

	public static void main(String[] args) throws Exception {
		StaticJavaParser.getConfiguration().setLanguageLevel(ParserConfiguration.LanguageLevel.JAVA_17);
		try (BufferedReader in = Files.newBufferedReader(Paths.get(args[0]), StandardCharsets.UTF_8);
				BufferedWriter out = Files.newBufferedWriter(Paths.get(args[1]), StandardCharsets.UTF_8)) {
			String line;
			while ((line = in.readLine()) != null) {
				if (line.isEmpty())
					continue;
				String[] parts = line.split("\t", 2);
				out.write(process(parts[0], parts[1]));
				out.write('\n');
			}
		}
	}

	private static String process(String id, String path) {
		StringBuilder sb = new StringBuilder();
		sb.append("{\"id\":").append(q(id));
		try {
			CompilationUnit cu;
			try {
				cu = StaticJavaParser.parse(new File(path));
			} catch (Throwable first) {
				// Fallback only for files that fail at JAVA_17: legacy code that uses '_' as an identifier (valid up
				// to Java 8, reserved since Java 9; ex.: ASM embedded in EclipseLink). Files that parse at JAVA_17
				// (all files of the pilot) are not affected.
				StaticJavaParser.getConfiguration().setLanguageLevel(ParserConfiguration.LanguageLevel.JAVA_8);
				try {
					cu = StaticJavaParser.parse(new File(path));
				} catch (Throwable second) {
					throw first;
				} finally {
					StaticJavaParser.getConfiguration().setLanguageLevel(ParserConfiguration.LanguageLevel.JAVA_17);
				}
			}
			String pkg = cu.getPackageDeclaration().map(p -> p.getNameAsString()).orElse("");
			List<String> items = new ArrayList<>();
			for (MethodDeclaration md : cu.findAll(MethodDeclaration.class)) {
				String owner = ownerChain(md);
				StringBuilder m = new StringBuilder();
				m.append("{\"pkg\":").append(q(pkg));
				m.append(",\"owner\":").append(owner == null ? "null" : q(owner));
				m.append(",\"name\":").append(q(md.getNameAsString()));
				m.append(",\"params\":[");
				boolean first = true;
				for (Parameter p : md.getParameters()) {
					if (!first)
						m.append(',');
					first = false;
					m.append(q(p.getType().asString() + (p.isVarArgs() ? "[]" : "")));
				}
				m.append("],\"sig\":").append(q(md.getSignature().asString()));
				m.append(",\"begin\":").append(md.getBegin().map(b -> b.line).orElse(-1));
				m.append(",\"end\":").append(md.getEnd().map(b -> b.line).orElse(-1));
				m.append(",\"abstract\":").append(!md.getBody().isPresent());
				m.append(",\"text\":").append(q(md.toString()));
				m.append('}');
				items.add(m.toString());
			}
			sb.append(",\"ok\":true,\"methods\":[").append(String.join(",", items)).append("]}");
		} catch (Throwable e) {
			String msg = String.valueOf(e.getMessage());
			if (msg.length() > 500)
				msg = msg.substring(0, 500);
			sb.append(",\"ok\":false,\"error\":").append(q(e.getClass().getSimpleName() + ": " + msg))
					.append(",\"methods\":[]}");
		}
		return sb.toString();
	}

	/** Chain of declaring types (Outer.Inner); null if inside an anonymous/local class. */
	private static String ownerChain(Node n) {
		List<String> names = new ArrayList<>();
		Optional<Node> p = n.getParentNode();
		while (p.isPresent()) {
			Node x = p.get();
			if (x instanceof ObjectCreationExpr || x instanceof LocalClassDeclarationStmt
					|| x instanceof LocalRecordDeclarationStmt)
				return null;
			if (x instanceof TypeDeclaration) {
				names.add(0, ((TypeDeclaration<?>) x).getNameAsString());
			}
			p = x.getParentNode();
		}
		return String.join(".", names);
	}

	private static String q(String s) {
		StringBuilder b = new StringBuilder(s.length() + 16).append('"');
		for (int i = 0; i < s.length(); i++) {
			char c = s.charAt(i);
			switch (c) {
			case '"': b.append("\\\""); break;
			case '\\': b.append("\\\\"); break;
			case '\n': b.append("\\n"); break;
			case '\r': b.append("\\r"); break;
			case '\t': b.append("\\t"); break;
			default:
				if (c < 0x20)
					b.append(String.format("\\u%04x", (int) c));
				else
					b.append(c);
			}
		}
		return b.append('"').toString();
	}
}
