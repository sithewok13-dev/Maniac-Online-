	if (!_scummverseRoaming) { warning("SCUMMVERSE_ZAK_PATHS_PASS enabled=0"); quitGame(); return; }
	Common::Path savedPath=ConfMan.getPath("path");
	// Simulate the default bare relative game path inside this probe's private cwd.
	if (symlink("@MANIAC@","maniac") || symlink("@ROOT@/zak","zak")) error("Cannot prepare relative path fixtures");
	ConfMan.setPath("path",Common::Path("maniac"));
	_scummverseZakMounted=false;
	if (!scummverseMountZak() || !scummverseMountAirport() || !scummverseMountStreet()) error("Relative Maniac path cannot discover sibling Zak");
	ConfMan.setPath("path",savedPath);
	ChRootFilesystemFactory sandbox("@ROOT@");
	Common::FSNode root=AbstractFSNode::makeFSNode(sandbox.makeRootFileNode());
	Common::FSNode folder=scummverseZakFolder(root);
	if (folder.getPath()!=Common::Path("/zak")) error("Sandbox Zak folder wrong");
	Common::Array<byte> bytes; Common::String problem;
	if (!readZakFile(folder,0,"7020931d5a2be0a49d68e7a1882363e4",bytes,problem) || bytes.size()!=1896) error("Sandbox index read failed or loose Maniac file shadowed it");
	if (!readZakFile(folder,1,"2e30571757edc1cd0f2a450ba5c89153",bytes,problem) || !readZakFile(folder,3,"25a9e059a9df572554ee8ceffc08cb9f",bytes,problem) || !readZakFile(folder,8,"5337090e7a6ebdbfb698ebda3750d926",bytes,problem)) error("Sandbox world resources inaccessible");
	if (scummverseZakFolder(root.getChild("case")).getName()!="Zak") error("Capitalized Zak folder not discovered");
	Common::FSNode missing=root.getChild("missing"), bad=root.getChild("bad");
	if (readZakFile(missing,0,"7020931d5a2be0a49d68e7a1882363e4",bytes,problem) || !problem.contains("/missing/00.LFL") || !problem.contains("missing")) error("Missing-file diagnosis failed");
	if (readZakFile(bad,0,"7020931d5a2be0a49d68e7a1882363e4",bytes,problem) || !problem.contains("/bad/00.LFL") || !problem.contains("does not match")) error("Wrong-edition diagnosis failed");
	if (readZakFile(root.getChild("absent"),0,"",bytes,problem) || !problem.contains("folder unavailable")) error("Missing-folder diagnosis failed");
	if (!readZakFile(root.getChild("Zak"),0,"7020931d5a2be0a49d68e7a1882363e4",bytes,problem)) error("Lowercase LFL not accepted");
	ConfMan.setPath("scummverse_zak_path",Common::Path("@ROOT@/missing"));
	_scummverseZakMounted=false;
	if (scummverseMountZak() || !_scummverseWorldNotice.contains("00.LFL")) error("Explicit override ignored or diagnostic lost");
	ConfMan.removeKey("scummverse_zak_path",ConfMan.getActiveDomainName());
	warning("SCUMMVERSE_ZAK_PATHS_PASS enabled=1"); quitGame();
