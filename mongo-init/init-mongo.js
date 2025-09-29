// /mongo-init/init-mongo.js

// Using print() is the standard way to log from mongo scripts.
// Docker will capture this standard output.
print("=== MongoDB Initialization Script Start ===");

const dbName = process.env.MONGO_INITDB_DATABASE;

if (!dbName) {
    printjson({ "error": "CRITICAL: MONGO_INITDB_DATABASE environment variable is not set." });
    quit(1); // Exit with a non-zero status code to indicate failure
}

try {
    db = db.getSiblingDB(dbName);
    print(`Successfully connected to database: ${dbName}`);

    print(`--- Creating users for ${dbName} ---`);

    // Create the ETL user (admin for this specific database)
    db.createUser({
        user: process.env.MONGO_INITDB_ROOT_USERNAME, 
        pwd: process.env.MONGO_INITDB_ROOT_PASSWORD,
        roles: [
            { role: 'readWrite', db: dbName }
        ]
    });
    print("✅ ETL user created successfully.");

    // Create the Analyst user (read-only for this specific database)
    db.createUser({
        user: process.env.MONGO_INITDB_ANALYST_USERNAME,
        pwd: process.env.MONGO_INITDB_ANALYST_PASSWORD,
        roles: [
            { role: 'read', db: dbName }
        ]
    });
    print("✅ Analyst user created successfully.");

    print("🎉 Initialization finished successfully.");

} catch (error) {
    printjson({ "error": "CRITICAL: An error occurred during database initialization.", "details": error.to_String() });
    quit(1);
}