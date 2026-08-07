const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const { exec, spawn } = require('child_process');
const fs = require('fs');

const app = express();

// Load environment variables from .env file if it exists
const envPath = path.join(__dirname, '../.env');
if (fs.existsSync(envPath)) {
    console.log('Loading environment variables from .env file...');
    const dotenvContent = fs.readFileSync(envPath, 'utf-8');
    dotenvContent.split(/\r?\n/).forEach(line => {
        const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
        if (match) {
            const key = match[1];
            let value = match[2] || '';
            if (value.startsWith('"') && value.endsWith('"')) value = value.slice(1, -1);
            if (value.startsWith("'") && value.endsWith("'")) value = value.slice(1, -1);
            process.env[key] = value.trim();
        }
    });
}

const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Serve static frontend files
app.use(express.static(path.join(__dirname, '../frontend')));

const dbPath = path.join(__dirname, 'skylark.db');

// Connect to SQLite Database
const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error('Error connecting to SQLite database:', err);
    } else {
        console.log('Connected to SQLite database.');
    }
});

// Helper function to run query-agent.py
function runQueryAgent(message, callback) {
    // Escape double quotes for shell arguments
    const escapedMsg = message.replace(/"/g, '\\"');
    
    // We execute python backend/query_agent.py "message"
    // Use path to python in the Cwd or default python env
    exec(`python "${path.join(__dirname, 'query_agent.py')}" "${escapedMsg}"`, (error, stdout, stderr) => {
        if (error) {
            console.error('exec error:', error);
            callback({ error: error.message });
            return;
        }
        try {
            const result = JSON.parse(stdout);
            callback(result);
        } catch (e) {
            console.error('Parsing error of python stdout:', e, 'Raw stdout:', stdout);
            callback({ error: 'Failed to parse agent response.', raw: stdout });
        }
    });
}

// 1. Chatbot endpoint
app.post('/api/chat', (req, res) => {
    const { message } = req.body;
    if (!message) {
        return res.status(400).json({ error: 'Message is required.' });
    }
    
    runQueryAgent(message, (result) => {
        if (result.error) {
            res.status(500).json(result);
        } else {
            res.json(result);
        }
    });
});

// 2. Monday.com Mock GraphQL v2 API endpoint
app.post('/v2', (req, res) => {
    // Run mock_graphql script by spawning python
    const pyProcess = spawn('python', [path.join(__dirname, 'run_graphql.py')]);
    
    let stdoutData = '';
    let stderrData = '';
    
    pyProcess.stdout.on('data', (data) => {
        stdoutData += data.toString();
    });
    
    pyProcess.stderr.on('data', (data) => {
        stderrData += data.toString();
    });
    
    pyProcess.on('close', (code) => {
        if (code !== 0) {
            console.error(`GraphQL runner process exited with code ${code}. Stderr: ${stderrData}`);
            return res.status(500).json({ error: 'Mock GraphQL execution failed.' });
        }
        try {
            const gqlResult = JSON.parse(stdoutData);
            res.json(gqlResult);
        } catch (e) {
            console.error('Error parsing GraphQL python stdout:', e, 'Raw:', stdoutData);
            res.status(500).json({ error: 'Failed to parse mock GraphQL response.' });
        }
    });
    
    // Write request body to stdin of the python script
    pyProcess.stdin.write(JSON.stringify(req.body));
    pyProcess.stdin.end();
});

// 3. Dashboard statistics endpoint
app.get('/api/dashboard', (req, res) => {
    const stats = {};
    
    // Get deals counts and total pipeline values
    db.all(`
        SELECT 
            deal_status, 
            COUNT(*) as count, 
            SUM(masked_deal_value) as value 
        FROM deals 
        GROUP BY deal_status
    `, [], (err, rows) => {
        if (err) {
            return res.status(500).json({ error: err.message });
        }
        
        stats.deals_status = rows;
        
        // Get sectoral breakdown
        db.all(`
            SELECT 
                sector_service, 
                SUM(masked_deal_value) as value,
                COUNT(*) as count
            FROM deals 
            GROUP BY sector_service
            ORDER BY value DESC
        `, [], (err, rows) => {
            if (err) return res.status(500).json({ error: err.message });
            stats.sector_deals = rows;
            
            // Get top owner sales ranking
            db.all(`
                SELECT 
                    owner_code, 
                    SUM(masked_deal_value) as value 
                FROM deals 
                WHERE deal_status = 'Won'
                GROUP BY owner_code 
                ORDER BY value DESC 
                LIMIT 5
            `, [], (err, rows) => {
                if (err) return res.status(500).json({ error: err.message });
                stats.owner_ranking = rows;
                
                // Get work order status breakdown
                db.all(`
                    SELECT 
                        execution_status, 
                        COUNT(*) as count,
                        SUM(amount_excl_gst) as value,
                        SUM(amount_receivable) as receivable
                    FROM work_orders 
                    GROUP BY execution_status
                `, [], (err, rows) => {
                    if (err) return res.status(500).json({ error: err.message });
                    stats.work_orders_status = rows;
                    res.json(stats);
                });
            });
        });
    });
});

// 4. Export CSV endpoint
app.get('/api/export', (req, res) => {
    const { type } = req.query; // 'deals' or 'work_orders'
    const fileName = type === 'work_orders' ? 'work_orders_data.csv' : 'deals_data.csv';
    const filePath = path.join(__dirname, '..', fileName);
    
    if (fs.existsSync(filePath)) {
        res.download(filePath, fileName);
    } else {
        res.status(404).json({ error: 'File not found.' });
    }
});

// 5. Get all deals raw data for table viewer
app.get('/api/deals', (req, res) => {
    db.all(`SELECT * FROM deals ORDER BY rowid ASC`, [], (err, rows) => {
        if (err) {
            return res.status(500).json({ error: err.message });
        }
        res.json(rows);
    });
});

// 6. Get all work orders raw data for table viewer
app.get('/api/work_orders', (req, res) => {
    db.all(`SELECT * FROM work_orders ORDER BY rowid ASC`, [], (err, rows) => {
        if (err) {
            return res.status(500).json({ error: err.message });
        }
        res.json(rows);
    });
});

// 7. Leadership Report data endpoint
app.get('/api/leadership-report', (req, res) => {
    const reportData = {};
    db.get("SELECT COUNT(*) as count, SUM(masked_deal_value) as sum FROM deals WHERE deal_status = 'Open'", [], (err, row) => {
        if (err) return res.status(500).json({ error: err.message });
        reportData.open_deals_count = row.count || 0;
        reportData.open_pipeline = row.sum || 0;

        db.get(`
            SELECT SUM(
                CASE WHEN closure_probability = 'High' THEN masked_deal_value * 0.8
                     WHEN closure_probability = 'Medium' THEN masked_deal_value * 0.5
                     WHEN closure_probability = 'Low' THEN masked_deal_value * 0.2
                     ELSE 0 END
            ) as weighted FROM deals WHERE deal_status = 'Open'
        `, [], (err, row) => {
            if (err) return res.status(500).json({ error: err.message });
            reportData.probability_weighted_revenue = row.weighted || 0;

            db.get("SELECT SUM(masked_deal_value) as sum FROM deals WHERE deal_status = 'Won'", [], (err, row) => {
                if (err) return res.status(500).json({ error: err.message });
                reportData.realized_won_revenue = row.sum || 0;

                db.get("SELECT COUNT(*) as count FROM work_orders WHERE execution_status = 'Completed'", [], (err, row) => {
                    if (err) return res.status(500).json({ error: err.message });
                    reportData.delivered_work_orders_count = row.count || 0;

                    db.get("SELECT SUM(billed_excl_gst) as sum FROM work_orders", [], (err, row) => {
                        if (err) return res.status(500).json({ error: err.message });
                        reportData.billed_work_order_value = row.sum || 0;

                        db.get("SELECT SUM(amount_receivable) as sum FROM work_orders", [], (err, row) => {
                            if (err) return res.status(500).json({ error: err.message });
                            reportData.outstanding_receivables = row.sum || 0;
                            res.json(reportData);
                        });
                    });
                });
            });
        });
    });
});

// Listen on port
app.listen(PORT, () => {
    console.log(`Server is running at http://localhost:${PORT}`);
});
