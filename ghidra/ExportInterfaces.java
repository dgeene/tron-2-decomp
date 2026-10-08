// Read-only evidence extraction: strings, references, selected functions, raw instructions.
// @category TRON
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.program.model.listing.Function;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashSet;
import java.util.regex.Pattern;

public class ExportInterfaces extends GhidraScript {
    private String field(Object value) {
        return String.valueOf(value).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ');
    }
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) throw new IllegalArgumentException("Expected OUTPUT_DIR [VA|xref:VA|define:VA ...]");
        Path out = Path.of(args[0]);
        Files.createDirectories(out);
        Files.deleteIfExists(out.resolve("COMPLETE"));
        var selected = new LinkedHashSet<Function>();
        int definitions = 0;
        try (var refs = Files.newBufferedWriter(out.resolve("requested-references.tsv"))) {
            refs.write("target_va\tfrom_va\tfunction_va\ttype\n");
            for (int i = 1; i < args.length; i++) {
                if (args[i].startsWith("xref:")) {
                    var address = toAddr(args[i].substring(5));
                    var references = currentProgram.getReferenceManager().getReferencesTo(address);
                    while (references.hasNext()) {
                        var ref = references.next();
                        Function f = getFunctionContaining(ref.getFromAddress());
                        refs.write(address + "\t" + ref.getFromAddress() + "\t" +
                            (f == null ? "" : f.getEntryPoint()) + "\t" + ref.getReferenceType() + "\n");
                        if (f != null) selected.add(f);
                    }
                } else {
                    boolean define = args[i].startsWith("define:");
                    var address = toAddr(define ? args[i].substring(7) : args[i]);
                    Function function = getFunctionContaining(address);
                    if (function == null && define) {
                        var block = currentProgram.getMemory().getBlock(address);
                        if (block == null || !block.isExecute()) throw new IllegalArgumentException("Not executable: " + address);
                        disassemble(address);
                        function = createFunction(address, "candidate_" + address);
                        definitions++;
                    }
                    if (function == null) throw new IllegalArgumentException("No function at " + args[i]);
                    selected.add(function);
                }
            }
        }
        Pattern interest = Pattern.compile("IClientShell|IServerShell|ILTClient|IClientFileMgr|IClientMgr|SetMasterDatabase|cshell\\.dll|object\\.lto|clientfx\\.fxd|cres\\.dll|sres\\.dll", Pattern.CASE_INSENSITIVE);
        Pattern interfaceName = Pattern.compile("[A-Za-z_][A-Za-z0-9_]+\\.(Default|Client|Server)");
        try (var strings = Files.newBufferedWriter(out.resolve("strings.tsv"));
             var refs = Files.newBufferedWriter(out.resolve("references.tsv"))) {
            strings.write("va\tvalue\n");
            refs.write("target_va\tfrom_va\tfunction_va\ttype\tvalue\n");
            var data = currentProgram.getListing().getDefinedData(true);
            while (data.hasNext()) {
                monitor.checkCancelled();
                var item = data.next();
                if (!(item.getValue() instanceof String)) continue;
                String value = (String)item.getValue();
                boolean relevant = interest.matcher(value).find();
                if (!relevant && !interfaceName.matcher(value).matches()) continue;
                strings.write(item.getAddress() + "\t" + field(value) + "\n");
                var references = currentProgram.getReferenceManager().getReferencesTo(item.getAddress());
                while (references.hasNext()) {
                    var ref = references.next();
                    Function function = getFunctionContaining(ref.getFromAddress());
                    refs.write(item.getAddress() + "\t" + ref.getFromAddress() + "\t" +
                        (function == null ? "" : function.getEntryPoint()) + "\t" + ref.getReferenceType() + "\t" + field(value) + "\n");
                    if (relevant && function != null) selected.add(function);
                }
            }
        }
        var functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext()) {
            Function f = functions.next();
            if (f.getName().matches("SetMasterDatabase|LTGetILTMemory|ObjectDLLSetup|fxGetNum|fxGetRef")) selected.add(f);
        }
        var decompiler = new DecompInterface();
        int successes = 0;
        try (var status = Files.newBufferedWriter(out.resolve("functions.tsv"))) {
            if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException(decompiler.getLastMessage());
            status.write("va\tname\tsuccess\tmessage\n");
            for (Function f : selected) {
                monitor.checkCancelled();
                var result = decompiler.decompileFunction(f, 45, monitor);
                boolean success = result.decompileCompleted() && result.getDecompiledFunction() != null;
                status.write(f.getEntryPoint() + "\t" + field(f.getName()) + "\t" + success + "\t" + field(result.getErrorMessage()) + "\n");
                if (success) {
                    successes++;
                    Files.writeString(out.resolve(f.getEntryPoint() + ".c"), result.getDecompiledFunction().getC());
                }
                try (var assembly = Files.newBufferedWriter(out.resolve(f.getEntryPoint() + ".asm"))) {
                    var instructions = currentProgram.getListing().getInstructions(f.getBody(), true);
                    while (instructions.hasNext()) {
                        var instruction = instructions.next();
                        assembly.write(instruction.getAddress() + "\t" + instruction + "\n");
                    }
                }
            }
        } finally { decompiler.dispose(); }
        Files.writeString(out.resolve("summary.txt"), "sha256=" + currentProgram.getExecutableSHA256() +
            "\nghidra=" + getGhidraVersion() + "\nselected=" + selected.size() + "\nsucceeded=" + successes +
            "\ntemporary_definitions=" + definitions + "\n");
        Files.writeString(out.resolve("COMPLETE"), "Evidence export completed. Check individual function status.\n");
    }
}
