import Foundation
import Security

let arguments = CommandLine.arguments
guard arguments.count == 4 else {
    fputs("usage: keychain_store.swift read|write SERVICE ACCOUNT\\n", stderr)
    exit(2)
}

let mode = arguments[1]
let service = arguments[2]
let account = arguments[3]
let query: [String: Any] = [
    kSecClass as String: kSecClassGenericPassword,
    kSecAttrService as String: service,
    kSecAttrAccount as String: account,
]

if mode == "read" {
    let readQuery = query.merging([
        kSecReturnData as String: true,
        kSecMatchLimit as String: kSecMatchLimitOne,
    ]) { _, newest in newest }
    var result: CFTypeRef?
    let readStatus = SecItemCopyMatching(readQuery as CFDictionary, &result)
    guard readStatus == errSecSuccess, let secret = result as? Data else {
        fputs("error: Keychain read failed (status \\(readStatus)).\\n", stderr)
        exit(1)
    }
    FileHandle.standardOutput.write(secret)
    exit(0)
}

guard mode == "write" else {
    fputs("error: Keychain mode must be read or write.\\n", stderr)
    exit(2)
}

let secret = FileHandle.standardInput.readDataToEndOfFile()
guard !secret.isEmpty else {
    fputs("error: Keychain secret must not be empty.\\n", stderr)
    exit(2)
}
let attributes: [String: Any] = [kSecValueData as String: secret]
let updateStatus = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)

if updateStatus == errSecItemNotFound {
    var newItem = query
    newItem[kSecValueData as String] = secret
    let addStatus = SecItemAdd(newItem as CFDictionary, nil)
    if addStatus != errSecSuccess {
        fputs("error: Keychain write failed (status \\(addStatus)).\\n", stderr)
        exit(1)
    }
} else if updateStatus != errSecSuccess {
    fputs("error: Keychain update failed (status \\(updateStatus)).\\n", stderr)
    exit(1)
}
