// Export an address catalog and bounded pseudocode samples for local study.
// @category TRON
import ghidra.app.util.headless.HeadlessScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.program.model.listing.Function;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashSet;

public class ExportAnalysis extends HeadlessScript {
    private String field(Object value) {
        return String.valueOf(value).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ');
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) throw new IllegalArgumentException("Expected OUTPUT_DIR SAMPLE_LIMIT (0 = all)");
        Path output = Path.of(args[0]);
        int limit = Integer.parseInt(args[1]);
        if (limit < 0) throw new IllegalArgumentException("SAMPLE_LIMIT must be nonnegative");
        Files.createDirectories(output);
        Files.deleteIfExists(output.resolve("COMPLETE"));
        Path pseudocode = output.resolve("pseudocode");
        Files.createDirectories(pseudocode);
        int count = 0;
        LinkedHashSet<Function> selected = new LinkedHashSet<>();
        var entryPoints = currentProgram.getSymbolTable().getExternalEntryPointIterator();
        while (entryPoints.hasNext()) {
            Function function = getFunctionAt(entryPoints.next());
            if (function != null && !function.isExternal()) selected.add(function);
        }
        try (var catalog = Files.newBufferedWriter(output.resolve("functions.tsv"), StandardCharsets.UTF_8)) {
            catalog.write("va\tname\tbody_bytes\tthunk\tsignature\n");
            var functions = currentProgram.getFunctionManager().getFunctions(true);
            while (functions.hasNext()) {
                monitor.checkCancelled();
                Function function = functions.next();
                count++;
                catalog.write(function.getEntryPoint() + "\t" + field(function.getName(true)) + "\t" +
                    function.getBody().getNumAddresses() + "\t" + function.isThunk() + "\t" +
                    field(function.getSignature()) + "\n");
                if (!function.isExternal() && !function.isThunk() && (limit == 0 || selected.size() < limit))
                    selected.add(function);
            }
        }
        DecompInterface decompiler = new DecompInterface();
        int attempted = 0;
        int succeeded = 0;
        try (var status = Files.newBufferedWriter(output.resolve("decompilation.tsv"), StandardCharsets.UTF_8)) {
            if (!decompiler.openProgram(currentProgram))
                throw new IllegalStateException(decompiler.getLastMessage());
            status.write("va\tname\tsuccess\tmessage\n");
            for (Function function : selected) {
                if (limit != 0 && attempted >= limit) break;
                monitor.checkCancelled();
                attempted++;
                var result = decompiler.decompileFunction(function, 30, monitor);
                boolean success = result.decompileCompleted() && result.getDecompiledFunction() != null;
                status.write(function.getEntryPoint() + "\t" + field(function.getName(true)) + "\t" +
                    success + "\t" + field(result.getErrorMessage()) + "\n");
                Path destination = pseudocode.resolve(function.getEntryPoint() + ".c");
                if (success) {
                    succeeded++;
                    Files.writeString(destination,
                        "/* Ghidra pseudocode: unreviewed, not buildable recovered C++. */\n" +
                        result.getDecompiledFunction().getC(), StandardCharsets.UTF_8);
                } else {
                    Files.deleteIfExists(destination);
                }
            }
        } finally {
            decompiler.dispose();
        }
        String summary = "program=" + currentProgram.getName() + "\nsha256=" + currentProgram.getExecutableSHA256() +
            "\nghidra=" + getGhidraVersion() + "\nlanguage=" + currentProgram.getLanguageID() +
            "\ncompiler=" + currentProgram.getCompilerSpec().getCompilerSpecID() +
            "\nanalysis_timeout=" + analysisTimeoutOccurred() + "\nfunctions=" + count +
            "\ndecompile_attempted=" + attempted + "\ndecompile_succeeded=" + succeeded + "\n";
        Files.writeString(output.resolve("summary.txt"), summary, StandardCharsets.UTF_8);
        if (!analysisTimeoutOccurred()) Files.writeString(output.resolve("COMPLETE"), "Export completed; see summary and per-function status.\n");
        println(summary);
    }
}
